import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  MenuItem,
  Grid,
  Chip,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { format } from 'date-fns';
import { getFindings } from '../services/api';
import { Finding, FindingSeverity } from '../types';

const severityColors = {
  [FindingSeverity.LOW]: 'success',
  [FindingSeverity.MEDIUM]: 'info',
  [FindingSeverity.HIGH]: 'warning',
  [FindingSeverity.CRITICAL]: 'error',
} as const;

const Findings: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    agent_name: '',
    severity: '',
    finding_type: '',
  });

  const { data: findings, isLoading } = useQuery(['findings', filters], () =>
    getFindings({
      ...filters,
      sort_by: 'timestamp',
      sort_desc: true,
    })
  );

  const columns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 70,
    },
    {
      field: 'timestamp',
      headerName: 'Time',
      width: 180,
      valueFormatter: (params) =>
        format(new Date(params.value), 'yyyy-MM-dd HH:mm:ss'),
    },
    {
      field: 'agent_name',
      headerName: 'Agent',
      width: 150,
    },
    {
      field: 'finding_type',
      headerName: 'Type',
      width: 150,
    },
    {
      field: 'severity',
      headerName: 'Severity',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={severityColors[params.value as FindingSeverity]}
          size="small"
        />
      ),
    },
    {
      field: 'message',
      headerName: 'Message',
      flex: 1,
    },
  ];

  const handleFilterChange = (field: string) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFilters((prev) => ({
      ...prev,
      [field]: event.target.value,
    }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Findings
      </Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Agent"
                value={filters.agent_name}
                onChange={handleFilterChange('agent_name')}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                label="Severity"
                value={filters.severity}
                onChange={handleFilterChange('severity')}
                size="small"
              >
                <MenuItem value="">All</MenuItem>
                {Object.values(FindingSeverity).map((severity) => (
                  <MenuItem key={severity} value={severity}>
                    {severity}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Type"
                value={filters.finding_type}
                onChange={handleFilterChange('finding_type')}
                size="small"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <div style={{ height: 600, width: '100%' }}>
            <DataGrid
              rows={findings || []}
              columns={columns}
              pageSize={10}
              rowsPerPageOptions={[10, 25, 50]}
              checkboxSelection
              disableSelectionOnClick
              loading={isLoading}
              onRowClick={(params) => navigate(`/findings/${params.row.id}`)}
            />
          </div>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Findings; 