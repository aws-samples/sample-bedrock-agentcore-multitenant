export const formatCurrency = (amount: number): string => {
  return `$${amount.toFixed(2)}`;
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString();
};

export const getInitials = (firstName: string, lastName: string): string => {
  return `${firstName.substring(0, 1)}${lastName.substring(0, 1)}`.toUpperCase();
};

export const getCurrentTimestamp = (): string => {
  return new Date().toLocaleTimeString();
};
