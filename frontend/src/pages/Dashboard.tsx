import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import {
  BugReport as BugReportIcon,
  Settings as SettingsIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { getAgents, getFindings } from '../services/api';
import { FindingSeverity } from '../types';

const Dashboard: React.FC = () => {
  const { data: agents, isLoading: agentsLoading } = useQuery(['agents'], () =>
    getAgents()
  );

  const { data: findings, isLoading: findingsLoading } = useQuery(['findings'], () =>
    getFindings({ limit: 100 })
  );

  const isLoading = agentsLoading || findingsLoading;

  const getSeverityCount = (severity: FindingSeverity) =>
    findings?.filter((f) => f.severity === severity).length || 0;

  const stats = [
    {
      title: 'Total Agents',
      value: agents?.length || 0,
      icon: <SettingsIcon sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: 'Active Findings',
      value: findings?.length || 0,
      icon: <BugReportIcon sx={{ fontSize: 40 }} />,
      color: '#dc004e',
    },
    {
      title: 'Critical Issues',
      value: getSeverityCount(FindingSeverity.CRITICAL),
      icon: <WarningIcon sx={{ fontSize: 40 }} />,
      color: '#f44336',
    },
    {
      title: 'Resolved Issues',
      value: findings?.filter((f) => f.severity === FindingSeverity.LOW).length || 0,
      icon: <CheckCircleIcon sx={{ fontSize: 40 }} />,
      color: '#4caf50',
    },
  ];

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="60vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        {stats.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.title}>
            <Card>
              <CardContent>
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="space-between"
                >
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4">{stat.value}</Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>{stat.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Dashboard; 