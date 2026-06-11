import React from 'react';
import { EmptyState } from './EmptyState';
import { Button } from './Button';
import { FolderOpen, Search, UserMinus } from 'lucide-react';

export default {
  title: 'UI/EmptyState',
  component: EmptyState,
};

const Template = (args) => <EmptyState {...args} />;

export const NoData = Template.bind({});
NoData.args = {
  icon: FolderOpen,
  title: 'No Invoices Found',
  subtitle: 'Get started by creating your first sales invoice to track user payments.',
  action: <Button variant="primary">Create Invoice</Button>,
};

export const NoResults = Template.bind({});
NoResults.args = {
  icon: Search,
  title: 'No Search Matches',
  subtitle: 'We could not find any customers matching that query. Check spelling or try a different filter.',
};

export const NoUsers = Template.bind({});
NoUsers.args = {
  icon: UserMinus,
  title: 'No Active Operators',
  subtitle: 'Please register standard operators to assign work shifts.',
  action: <Button variant="secondary">Add Operator</Button>,
};
