import React from 'react';
import { Badge } from './Badge';
import { CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';

export default {
  title: 'UI/Badge',
  component: Badge,
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['success', 'warning', 'error', 'info', 'neutral'],
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
    },
    onDismiss: { action: 'dismissed' },
  },
};

const Template = (args) => <Badge {...args} />;

export const Success = Template.bind({});
Success.args = {
  children: 'Paid Invoice',
  variant: 'success',
  icon: CheckCircle,
};

export const Warning = Template.bind({});
Warning.args = {
  children: 'Pending Approval',
  variant: 'warning',
  icon: AlertTriangle,
};

export const Error = Template.bind({});
Error.args = {
  children: 'Failed Sync',
  variant: 'error',
  icon: XCircle,
};

export const InfoVariant = Template.bind({});
InfoVariant.args = {
  children: 'Active Connection',
  variant: 'info',
  icon: Info,
};

export const Dismissible = Template.bind({});
Dismissible.args = {
  children: 'Clearable Filter',
  variant: 'neutral',
  onDismiss: () => alert('Dismiss trigger'),
};
