import React, { useState } from 'react';
import { Input } from './Input';
import { Mail, Lock, Search } from 'lucide-react';

export default {
  title: 'UI/Input',
  component: Input,
  argTypes: {
    disabled: { control: 'boolean' },
    required: { control: 'boolean' },
    valid: { control: 'boolean' },
  },
};

const Template = (args) => {
  const [val, setVal] = useState('');
  return (
    <div style={{ maxWidth: '360px' }}>
      <Input 
        {...args} 
        value={val} 
        onChange={setVal} 
        onClear={() => setVal('')} 
      />
    </div>
  );
};

export const Basic = Template.bind({});
Basic.args = {
  label: 'Username',
  placeholder: 'Enter your username',
  helperText: 'Username must be unique.',
};

export const Email = Template.bind({});
Email.args = {
  label: 'Email Address',
  type: 'email',
  placeholder: 'you@example.com',
  iconLeft: Mail,
};

export const Invalid = Template.bind({});
Invalid.args = {
  label: 'Password',
  type: 'password',
  placeholder: '••••••••',
  iconLeft: Lock,
  error: 'Password must be at least 8 characters long.',
};

export const Valid = Template.bind({});
Valid.args = {
  label: 'Search Query',
  placeholder: 'Search products...',
  iconLeft: Search,
  valid: true,
};
