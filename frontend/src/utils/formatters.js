export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return '₹0.00';
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

export const formatIndianNumber = (num) => {
  if (num === null || num === undefined) return '0';
  
  return new Intl.NumberFormat('en-IN').format(num);
};

export const formatCompactCurrency = (amount) => {
  if (amount === null || amount === undefined) return '₹0';
  
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  } else if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(2)} L`;
  } else if (amount >= 1000) {
    return `₹${(amount / 1000).toFixed(2)} K`;
  }
  return formatCurrency(amount);
};