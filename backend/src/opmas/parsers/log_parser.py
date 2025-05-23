import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Pattern, Tuple

from ..core.config import ConfigManager
from ..core.logging import LogManager
from ..data_models import ParsedLogEvent
from ..utils.nats import NATSClient

logger = LogManager().get_logger(__name__)

class LogParser:
    """Handles log parsing, classification, and enrichment."""
    
    def __init__(self):
        self.config = ConfigManager().get_config()
        self.nats_client = NATSClient()
        self.compiled_rules: Dict[str, List[Tuple[Pattern, bool]]] = {}
        self._compile_rules()
        
    def _compile_rules(self):
        """Compile regex patterns for log parsing rules."""
        # Basic syslog format patterns
        self.compiled_rules['syslog'] = [
            (re.compile(r'<(\d+)>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)) (\S+) (\S+) (\S+): (.+)'), True),
            (re.compile(r'<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}) (\S+) (\S+)(?:\[(\d+)\])?: (.+)'), True)
        ]
        
        # Domain-specific patterns
        self.compiled_rules['wifi'] = [
            (re.compile(r'wlan\d+: STA ([0-9a-fA-F:]+) (authenticated|deauthenticated|disassociated)'), True),
            (re.compile(r'wlan\d+: AP-STA-([0-9a-fA-F:]+) (connected|disconnected)'), True)
        ]
        
        self.compiled_rules['security'] = [
            (re.compile(r'(?:dropbear|sshd)(?:\[\d+\])?: (?:Failed|Invalid) (?:password|key) for (\S+) from (\d+\.\d+\.\d+\.\d+)'), True),
            (re.compile(r'iptables: (?:DROP|REJECT) .* SRC=(\d+\.\d+\.\d+\.\d+)'), True)
        ]
        
        self.compiled_rules['connectivity'] = [
            (re.compile(r'interface (\w+) (?:up|down)'), True),
            (re.compile(r'DHCP(?:ACK|DISCOVER|REQUEST) \((\w+)\) (\d+\.\d+\.\d+\.\d+)'), True)
        ]
        
        self.compiled_rules['health'] = [
            (re.compile(r'OOM killer invoked'), False),
            (re.compile(r'kernel: (?:Out of memory|oom-killer)'), False),
            (re.compile(r'(?:jffs2|ubifs): (?:error|corruption)'), False)
        ]
        
    def _classify_log(self, event: ParsedLogEvent) -> str:
        """Classify log based on process name and message content."""
        process_name = event.process_name.lower() if event.process_name else ""
        message = event.message.lower()
        
        # Process-based classification
        if process_name in ['hostapd', 'wpa_supplicant']:
            return 'wifi'
        elif process_name in ['dropbear', 'sshd', 'firewall']:
            return 'security'
        elif process_name in ['netifd', 'pppd', 'odhcp6c', 'odhcpd']:
            return 'connectivity'
        elif process_name == 'kernel':
            # Kernel messages need content inspection
            if any(pattern.search(message) for pattern, _ in self.compiled_rules['health']):
                return 'health'
            elif 'wlan' in message or 'wifi' in message:
                return 'wifi'
            elif 'iptables' in message or 'firewall' in message:
                return 'security'
            elif 'interface' in message or 'dhcp' in message:
                return 'connectivity'
        
        # Content-based classification if process name doesn't match
        for domain, patterns in self.compiled_rules.items():
            if any(pattern.search(message) for pattern, _ in patterns):
                return domain
                
        return 'system'  # Default classification
        
    def _enrich_log(self, event: ParsedLogEvent) -> None:
        """Enrich log with additional context and extracted fields."""
        if not event.structured_fields:
            event.structured_fields = {}
            
        # Extract fields based on domain-specific patterns
        domain = event.log_source_type
        if domain in self.compiled_rules:
            for pattern, _ in self.compiled_rules[domain]:
                match = pattern.search(event.message)
                if match:
                    # Store matched groups in structured fields
                    groups = match.groups()
                    if groups:
                        event.structured_fields[f'{domain}_extracted'] = {
                            'groups': groups,
                            'pattern': pattern.pattern
                        }
                    break
                    
        # Add metadata
        event.structured_fields['metadata'] = {
            'parser_version': '1.0',
            'parsed_at': datetime.utcnow().isoformat(),
            'source_type': 'syslog'
        }
        
    async def process_log(self, raw_event: Dict) -> Optional[ParsedLogEvent]:
        """Process a raw log event."""
        try:
            # Create ParsedLogEvent from raw event
            event = ParsedLogEvent.from_dict(raw_event)
            
            # Classify the log
            event.log_source_type = self._classify_log(event)
            
            # Enrich with additional context
            self._enrich_log(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing log event: {e}")
            return None
            
    async def start(self):
        """Start the log parser service."""
        await self.nats_client.connect()
        
        # Subscribe to raw parsed logs
        await self.nats_client.subscribe(
            "logs.parsed.raw",
            self._handle_raw_log
        )
        
        logger.info("Log parser service started")
        
    async def _handle_raw_log(self, msg):
        """Handle incoming raw log messages."""
        try:
            # Parse message data
            data = json.loads(msg.data.decode())
            
            # Process the log
            event = await self.process_log(data)
            if not event:
                return
                
            # Publish to domain-specific topic
            topic = f"logs.{event.log_source_type}"
            await self.nats_client.publish(
                topic,
                json.dumps(event.to_dict()).encode()
            )
            
            logger.debug(f"Published log to {topic}: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Error handling raw log: {e}")
            
    async def stop(self):
        """Stop the log parser service."""
        await self.nats_client.close()
        logger.info("Log parser service stopped") 