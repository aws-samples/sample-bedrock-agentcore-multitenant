import React from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Table from '@cloudscape-design/components/table';
import Badge from '@cloudscape-design/components/badge';
import Box from '@cloudscape-design/components/box';

interface Claim {
  claim_id: number;
  claim_number: string;
  customer_name: string;
  claim_amount: number;
  claim_date: string;
  status: string;
  description?: string;
}

interface ClaimsTableProps {
  claims: Claim[];
}

export const ClaimsTable: React.FC<ClaimsTableProps> = ({ claims }) => {
  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Structured data with Row-Level Security (RLS)"
        >
          Your Insurance Claims
        </Header>
      }
    >
      <Table
        columnDefinitions={[
          {
            id: 'claim_number',
            header: 'Claim Number',
            cell: (item: Claim) => item.claim_number
          },
          {
            id: 'customer_name',
            header: 'Customer',
            cell: (item: Claim) => item.customer_name
          },
          {
            id: 'claim_amount',
            header: 'Amount',
            cell: (item: Claim) => `$${item.claim_amount}`
          },
          {
            id: 'claim_date',
            header: 'Date',
            cell: (item: Claim) => new Date(item.claim_date).toLocaleDateString()
          },
          {
            id: 'status',
            header: 'Status',
            cell: (item: Claim) => (
              <Badge
                color={
                  item.status === 'approved' ? 'green' :
                  item.status === 'pending' ? 'blue' : 'red'
                }
              >
                {item.status}
              </Badge>
            )
          }
        ]}
        items={claims}
        loadingText="Loading claims"
        empty={
          <Box textAlign="center" color="inherit">
            <b>No claims</b>
            <Box padding={{ bottom: 's' }} variant="p" color="inherit">
              No claims to display.
            </Box>
          </Box>
        }
      />
    </Container>
  );
};
