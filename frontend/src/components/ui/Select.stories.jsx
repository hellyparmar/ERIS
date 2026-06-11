import React, { useState } from 'react';
import { Select } from './Select';

export default {
  title: 'UI/Select',
  component: Select,
  argTypes: {
    disabled: { control: 'boolean' },
    required: { control: 'boolean' },
    searchable: { control: 'boolean' },
  },
};

const options = [
  { label: 'Option 1 - Starter Plan', value: 'starter' },
  { label: 'Option 2 - Growth Plan', value: 'growth' },
  { label: 'Option 3 - Enterprise Suite', value: 'enterprise' },
  { label: 'Option 4 - Special Custom Plan', value: 'custom' },
];

const Template = (args) => {
  const [val, setVal] = useState('');
  return (
    <div style={{ maxWidth: '320px' }}>
      <Select 
        {...args} 
        value={val} 
        onChange={setVal} 
      />
    </div>
  );
};

export const Basic = Template.bind({});
Basic.args = {
  label: 'Subscription Plan',
  options,
  placeholder: 'Select plan level',
};

export const Searchable = Template.bind({});
Searchable.args = {
  label: 'Select Outlet Location',
  options,
  searchable: true,
  placeholder: 'Search & select...',
};

export const WithError = Template.bind({});
WithError.args = {
  label: 'Choose Billing Cycle',
  options,
  error: 'Billing cycle selection is required to proceed.',
};
