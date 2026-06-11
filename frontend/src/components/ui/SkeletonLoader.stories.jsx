import React from 'react';
import { SkeletonLoader } from './SkeletonLoader';

export default {
  title: 'UI/SkeletonLoader',
  component: SkeletonLoader,
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['text', 'avatar', 'card', 'table'],
    },
    count: { control: 'number' },
  },
};

const Template = (args) => <SkeletonLoader {...args} />;

export const Text = Template.bind({});
Text.args = {
  variant: 'text',
  count: 3,
  width: '100%',
};

export const Avatar = Template.bind({});
Avatar.args = {
  variant: 'avatar',
  height: '48px',
};

export const Card = Template.bind({});
Card.args = {
  variant: 'card',
  width: '320px',
};

export const Table = Template.bind({});
Table.args = {
  variant: 'table',
  count: 5,
};
