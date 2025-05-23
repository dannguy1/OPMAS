import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Grid,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  getAgent,
  getAgentRules,
  createAgentRule,
  updateAgentRule,
  deleteAgentRule,
} from '../services/api';
import { Agent, AgentRule, FindingSeverity } from '../types';

const severityColors = {
  [FindingSeverity.LOW]: 'success',
  [FindingSeverity.MEDIUM]: 'info',
  [FindingSeverity.HIGH]: 'warning',
  [FindingSeverity.CRITICAL]: 'error',
} as const;

const AgentDetails: React.FC = () => {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [openDialog, setOpenDialog] = useState(false);
  const [editingRule, setEditingRule] = useState<AgentRule | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    pattern: '',
    severity: FindingSeverity.MEDIUM,
    enabled: true,
    cooldown_seconds: 300,
    threshold: 1,
  });

  const { data: agent, isLoading: agentLoading } = useQuery(
    ['agent', name],
    () => getAgent(name!)
  );

  const { data: rules, isLoading: rulesLoading } = useQuery(
    ['agent-rules', name],
    () => getAgentRules(name!)
  );

  const createMutation = useMutation(
    (data: Omit<AgentRule, 'id' | 'agent_id' | 'created_at' | 'updated_at'>) =>
      createAgentRule(name!, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['agent-rules', name]);
        setOpenDialog(false);
        resetForm();
      },
    }
  );

  const updateMutation = useMutation(
    (data: { ruleName: string; rule: Partial<AgentRule> }) =>
      updateAgentRule(name!, data.ruleName, data.rule),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['agent-rules', name]);
        setOpenDialog(false);
        resetForm();
      },
    }
  );

  const deleteMutation = useMutation(
    (ruleName: string) => deleteAgentRule(name!, ruleName),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['agent-rules', name]);
      },
    }
  );

  const handleOpenDialog = (rule?: AgentRule) => {
    if (rule) {
      setEditingRule(rule);
      setFormData({
        name: rule.name,
        description: rule.description,
        pattern: rule.pattern,
        severity: rule.severity,
        enabled: rule.enabled,
        cooldown_seconds: rule.cooldown_seconds,
        threshold: rule.threshold,
      });
    } else {
      resetForm();
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    resetForm();
  };

  const resetForm = () => {
    setEditingRule(null);
    setFormData({
      name: '',
      description: '',
      pattern: '',
      severity: FindingSeverity.MEDIUM,
      enabled: true,
      cooldown_seconds: 300,
      threshold: 1,
    });
  };

  const handleSubmit = () => {
    if (editingRule) {
      updateMutation.mutate({
        ruleName: editingRule.name,
        rule: formData,
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = (ruleName: string) => {
    if (window.confirm('Are you sure you want to delete this rule?')) {
      deleteMutation.mutate(ruleName);
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      width: 200,
    },
    {
      field: 'description',
      headerName: 'Description',
      width: 300,
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
      field: 'enabled',
      headerName: 'Enabled',
      width: 100,
      renderCell: (params) => (
        <Switch checked={params.value} disabled />
      ),
    },
    {
      field: 'cooldown_seconds',
      headerName: 'Cooldown',
      width: 120,
      valueFormatter: (params) => `${params.value}s`,
    },
    {
      field: 'threshold',
      headerName: 'Threshold',
      width: 100,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleOpenDialog(params.row)}
          >
            <EditIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDelete(params.row.name)}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  if (agentLoading || rulesLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="60vh"
      >
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  if (!agent) {
    return (
      <Box>
        <Typography variant="h5" color="error">
          Agent not found
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/agents')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4">{agent.name}</Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Agent Details
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    Package Name
                  </Typography>
                  <Typography variant="body1">{agent.package_name}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    Status
                  </Typography>
                  <Chip
                    label={agent.status}
                    color={
                      agent.status === 'running'
                        ? 'success'
                        : agent.status === 'stopped'
                        ? 'warning'
                        : 'error'
                    }
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography color="textSecondary" gutterBottom>
                    Subscribed Topics
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {agent.subscribed_topics.map((topic) => (
                      <Chip key={topic} label={topic} size="small" />
                    ))}
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Rules</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Add Rule
            </Button>
          </Box>
          <Card>
            <CardContent>
              <div style={{ height: 600, width: '100%' }}>
                <DataGrid
                  rows={rules || []}
                  columns={columns}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  checkboxSelection
                  disableSelectionOnClick
                  loading={rulesLoading}
                />
              </div>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingRule ? 'Edit Rule' : 'Add Rule'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Name"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              margin="normal"
              disabled={!!editingRule}
            />
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              margin="normal"
              multiline
              rows={2}
            />
            <TextField
              fullWidth
              label="Pattern"
              value={formData.pattern}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, pattern: e.target.value }))
              }
              margin="normal"
              multiline
              rows={2}
              helperText="Regular expression pattern"
            />
            <TextField
              fullWidth
              select
              label="Severity"
              value={formData.severity}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  severity: e.target.value as FindingSeverity,
                }))
              }
              margin="normal"
              SelectProps={{
                native: true,
              }}
            >
              {Object.values(FindingSeverity).map((severity) => (
                <option key={severity} value={severity}>
                  {severity}
                </option>
              ))}
            </TextField>
            <TextField
              fullWidth
              type="number"
              label="Cooldown (seconds)"
              value={formData.cooldown_seconds}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  cooldown_seconds: parseInt(e.target.value),
                }))
              }
              margin="normal"
            />
            <TextField
              fullWidth
              type="number"
              label="Threshold"
              value={formData.threshold}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  threshold: parseInt(e.target.value),
                }))
              }
              margin="normal"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      enabled: e.target.checked,
                    }))
                  }
                />
              }
              label="Enabled"
              sx={{ mt: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.name || !formData.pattern}
          >
            {editingRule ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentDetails; 