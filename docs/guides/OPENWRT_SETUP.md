# Configuring OpenWRT Log Forwarding for OPMAS

This document describes how to configure an OpenWRT device to forward its system logs to the OPMAS Log Ingestor component.

**Target:** OpenWRT (recent versions recommended, using `logd` as the default syslog daemon).

**Goal:** Send logs via the network to the machine running the OPMAS Log Ingestor (listening on UDP port 514 by default, or TCP port 1514 if configured).

---

## Prerequisites

1.  **OPMAS Log Ingestor Running:** Ensure the OPMAS system is running, specifically the `log_ingestor` component, and note its IP address and listening port (default: UDP 514).
2.  **Network Connectivity:** The OpenWRT device must be able to reach the OPMAS Log Ingestor's IP address over the network.
3.  **SSH/Web UI Access:** You need access to the OpenWRT device's command line (via SSH) or its web interface (LuCI) to modify settings.

---

## Configuration Steps (Using Command Line / SSH)

This is generally the most reliable way.

1.  **SSH into your OpenWRT device:**
    ```bash
    ssh root@<your-openwrt-device-ip>
    ```

2.  **Edit the system configuration file:**
    Use `vi` or your preferred editor to modify `/etc/config/system`.
    ```bash
    vi /etc/config/system
    ```

3.  **Find the `config system` section:**
    It usually looks something like this:
    ```uci
    config system
        option hostname 'OpenWRT-Router1'
        option timezone 'UTC'
        # ... other options ...
    ```

4.  **Add or modify log forwarding options:**
    Add the following options within the `config system` section. Replace `<OPMAS_INGESTOR_IP>` with the actual IP address of the machine running OPMAS.

    *   **`option log_ip <OPMAS_INGESTOR_IP>`**: Specifies the remote IP address.
    *   **`option log_port '514'`**: Specifies the remote port (use 514 for UDP, or the configured TCP port if using TCP).
    *   **`option log_proto 'udp'`**: Specifies the protocol (use `udp` or `tcp`). UDP is simpler initially. TCP is more reliable but might require installing `syslog-ng` if `logd` doesn't support TCP forwarding well.
    *   **(Optional) `option log_remote '1'`**: Ensure remote logging is explicitly enabled (often the default if `log_ip` is set).

    The section should look similar to this afterwards:
    ```uci
    config system
        option hostname 'OpenWRT-Router1'
        option timezone 'UTC'
        # ... other options ...
        option log_ip '<OPMAS_INGESTOR_IP>'
        option log_port '514'
        option log_proto 'udp'
        option log_remote '1'
    ```

5.  **Save the changes and exit the editor.**
    (In `vi`, press `Esc`, then type `:wq` and press `Enter`).

6.  **Apply the configuration changes:**
    ```bash
    uci commit system
    ```

7.  **Restart the log daemon:**
    ```bash
    /etc/init.d/log restart
    ```

8.  **Verify:**
    Check the OPMAS Log Ingestor logs on the receiving machine. You should start seeing syslog messages arriving from your OpenWRT device's IP address.
You can also check the OpenWRT system log for confirmation or errors:
    ```bash
    logread | grep logd
    ```

---

## Configuration Steps (Using LuCI Web Interface)

1.  Log in to the LuCI web interface.
2.  Navigate to **System -> System**.
3.  Go to the **Logging** tab.
4.  Enter the IP address of the OPMAS Log Ingestor machine in the **"Remote system log server"** field.
5.  Enter the correct port (e.g., `514`) in the **"Remote system log server port"** field.
6.  Select the **"Protocol for remote system log server"** (usually UDP).
7.  Ensure the **"Enable logging to remote server"** checkbox is checked (it might be implicitly enabled when an IP is entered).
8.  Click **"Save & Apply"**.

---

## Important Notes

*   **Firewall:** Ensure no firewall rules on the OpenWRT device or the OPMAS host machine are blocking the syslog traffic (UDP/514 or the configured TCP port).
*   **Log Levels:** By default, OpenWRT might not log everything verbosely. You might need to adjust log levels for specific services (e.g., `hostapd`) in their respective configurations if you need more detailed logs for certain agent rules.
*   **TCP/TLS:** For more reliable delivery, especially over less stable networks, TCP is preferred. For security, using `syslog-ng` with TLS encryption would be ideal, but this requires more setup on both OpenWRT and the OPMAS ingestor.
*   **Resource Usage:** Continuously forwarding logs uses some network bandwidth and CPU resources on the OpenWRT device, though generally minimal. 