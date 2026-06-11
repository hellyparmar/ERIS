import React from 'react';
import { Card } from './Card';
import { Button } from './Button';

export default {
  title: 'UI/Card',
  component: Card,
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['base', 'elevated', 'bordered'],
    },
    onClick: { action: 'clicked' },
  },
};

const Template = (args) => (
  <div style={{ maxWidth: '400px' }}>
    <Card {...args}>
      <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px', margin: 0 }}>
        The Enterprise Retail Intelligence System provides modern data visualization, POS operations management, and secure employee scheduling tools inside a consolidated workspace.
      </p>
    </Card>
  </div>
);

export const Base = Template.bind({});
Base.args = {
  title: 'Store Performance',
  variant: 'base',
  titleRight: <Button size="sm" variant="ghost">View Details</Button>,
};

export const Elevated = Template.bind({});
Elevated.args = {
  title: 'Terminal Configurations',
  variant: 'elevated',
};

export const Bordered = Template.bind({});
Bordered.args = {
  title: 'Active Alerts',
  variant: 'bordered',
};
