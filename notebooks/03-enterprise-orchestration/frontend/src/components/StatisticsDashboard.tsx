import React from 'react';
import Container from '@cloudscape-design/components/container';
import ColumnLayout from '@cloudscape-design/components/column-layout';
import Box from '@cloudscape-design/components/box';

interface Statistics {
  total_claims: number;
  total_amount: number;
  approved_count: number;
  recent_claims: number;
}

interface StatisticsDashboardProps {
  statistics: Statistics;
}

export const StatisticsDashboard: React.FC<StatisticsDashboardProps> = ({ statistics }) => {
  return (
    <Container>
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">Total Claims</Box>
          <Box variant="awsui-value-large">{statistics.total_claims}</Box>
        </div>
        <div>
          <Box variant="awsui-key-label">Total Amount</Box>
          <Box variant="awsui-value-large">
            ${statistics.total_amount?.toFixed(2) || '0.00'}
          </Box>
        </div>
        <div>
          <Box variant="awsui-key-label">Approved</Box>
          <Box variant="awsui-value-large">{statistics.approved_count}</Box>
        </div>
        <div>
          <Box variant="awsui-key-label">Last 7 Days</Box>
          <Box variant="awsui-value-large">{statistics.recent_claims}</Box>
        </div>
      </ColumnLayout>
    </Container>
  );
};
