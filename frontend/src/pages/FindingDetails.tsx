import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  CircularProgress,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import { getFinding, deleteFinding } from '../services/api';
import { FindingSeverity } from '../types';

const severityColors = {
  [FindingSeverity.LOW]: 'success',
  [FindingSeverity.MEDIUM]: 'info',
  [FindingSeverity.HIGH]: 'warning',
  [FindingSeverity.CRITICAL]: 'error',
} as const;

const FindingDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: finding, isLoading } = useQuery(['finding', id], () =>
    getFinding(Number(id))
  );

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this finding?')) {
      await deleteFinding(Number(id));
      navigate('/findings');
    }
  };

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

  if (!finding) {
    return (
      <Box>
        <Typography variant="h5" color="error">
          Finding not found
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/findings')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4">Finding Details</Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    ID
                  </Typography>
                  <Typography variant="body1">{finding.id}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    Timestamp
                  </Typography>
                  <Typography variant="body1">
                    {format(new Date(finding.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    Agent
                  </Typography>
                  <Typography variant="body1">{finding.agent_name}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    Type
                  </Typography>
                  <Typography variant="body1">{finding.finding_type}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    Severity
                  </Typography>
                  <Chip
                    label={finding.severity}
                    color={severityColors[finding.severity]}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography color="textSecondary" gutterBottom>
                    Resource ID
                  </Typography>
                  <Typography variant="body1">{finding.resource_id}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography color="textSecondary" gutterBottom>
                    Message
                  </Typography>
                  <Typography variant="body1">{finding.message}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography color="textSecondary" gutterBottom>
                    Details
                  </Typography>
                  <Card variant="outlined">
                    <CardContent>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(finding.details, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box mt={3} display="flex" justifyContent="flex-end">
        <Button
          variant="contained"
          color="error"
          onClick={handleDelete}
        >
          Delete Finding
        </Button>
      </Box>
    </Box>
  );
};

export default FindingDetails; 