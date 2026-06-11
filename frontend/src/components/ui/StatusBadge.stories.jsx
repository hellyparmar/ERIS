import React from 'react';
import { StatusBadge } from './StatusBadge';

export default {
  title: 'UI/StatusBadge',
  component: StatusBadge,
  argTypes: {
    status: {
      control: { type: 'select' },
      options: ['paid', 'success', 'pending', 'warning', 'failed', 'error', 'processing'],
    },
    pulse: { control: 'boolean' },
  },
};

const Template = (args) => <StatusBadge {...args} />;

export const Paid = Template.bind({});
Paid.args = {
  status: 'paid',
};

export const Pending = Template.bind({});
Pending.args = {
  status: 'pending',
  pulse: true,
};

export const Failed = Template.bind({});
Failed.args = {
  status: 'failed',
};

export const Processing = Template.bind({});
Processing.args = {
  status: 'processing',
};
