import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { getAgents, createAgent, updateAgent, deleteAgent } from '../services/api';
import { Agent, AgentStatus } from '../types';

const statusColors = {
  [AgentStatus.RUNNING]: 'success',
  [AgentStatus.STOPPED]: 'warning',
  [AgentStatus.ERROR]: 'error',
} as const;

const Agents: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [openDialog, setOpenDialog] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    package_name: '',
    subscribed_topics: '',
    enabled: true,
  });

  const { data: agents, isLoading } = useQuery(['agents'], getAgents);

  const createMutation = useMutation(createAgent, {
    onSuccess: () => {
      queryClient.invalidateQueries(['agents']);
      setOpenDialog(false);
      resetForm();
    },
  });

  const updateMutation = useMutation(
    (data: { name: string; agent: Partial<Agent> }) =>
      updateAgent(data.name, data.agent),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['agents']);
        setOpenDialog(false);
        resetForm();
      },
    }
  );

  const deleteMutation = useMutation(deleteAgent, {
    onSuccess: () => {
      queryClient.invalidateQueries(['agents']);
    },
  });

  const handleOpenDialog = (agent?: Agent) => {
    if (agent) {
      setEditingAgent(agent);
      setFormData({
        name: agent.name,
        package_name: agent.package_name,
        subscribed_topics: agent.subscribed_topics.join(', '),
        enabled: agent.enabled,
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
    setEditingAgent(null);
    setFormData({
      name: '',
      package_name: '',
      subscribed_topics: '',
      enabled: true,
    });
  };

  const handleSubmit = () => {
    const agentData = {
      ...formData,
      subscribed_topics: formData.subscribed_topics
        .split(',')
        .map((topic) => topic.trim())
        .filter(Boolean),
    };

    if (editingAgent) {
      updateMutation.mutate({
        name: editingAgent.name,
        agent: agentData,
      });
    } else {
      createMutation.mutate(agentData);
    }
  };

  const handleDelete = (name: string) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      deleteMutation.mutate(name);
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      width: 200,
    },
    {
      field: 'package_name',
      headerName: 'Package',
      width: 200,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={statusColors[params.value as AgentStatus]}
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

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Agents</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Agent
        </Button>
      </Box>

      <Card>
        <CardContent>
          <div style={{ height: 600, width: '100%' }}>
            <DataGrid
              rows={agents || []}
              columns={columns}
              pageSize={10}
              rowsPerPageOptions={[10, 25, 50]}
              checkboxSelection
              disableSelectionOnClick
              loading={isLoading}
              onRowClick={(params) => navigate(`/agents/${params.row.name}`)}
            />
          </div>
        </CardContent>
      </Card>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingAgent ? 'Edit Agent' : 'Add Agent'}
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
              disabled={!!editingAgent}
            />
            <TextField
              fullWidth
              label="Package Name"
              value={formData.package_name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, package_name: e.target.value }))
              }
              margin="normal"
            />
            <TextField
              fullWidth
              label="Subscribed Topics (comma-separated)"
              value={formData.subscribed_topics}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  subscribed_topics: e.target.value,
                }))
              }
              margin="normal"
              helperText="Enter topics separated by commas"
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
            disabled={!formData.name || !formData.package_name}
          >
            {editingAgent ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Agents; 