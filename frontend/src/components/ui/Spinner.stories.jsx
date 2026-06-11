import React from 'react';
import { Spinner } from './Spinner';

export default {
  title: 'UI/Spinner',
  component: Spinner,
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
    },
    color: { control: 'color' },
  },
};

const Template = (args) => <Spinner {...args} />;

export const Small = Template.bind({});
Small.args = {
  size: 'sm',
};

export const Medium = Template.bind({});
Medium.args = {
  size: 'md',
};

export const Large = Template.bind({});
Large.args = {
  size: 'lg',
};

export const CustomColor = Template.bind({});
CustomColor.args = {
  size: 'lg',
  color: 'var(--accent-cyan)',
};
