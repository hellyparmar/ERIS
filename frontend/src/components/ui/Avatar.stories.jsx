import React from 'react';
import { Avatar } from './Avatar';

export default {
  title: 'UI/Avatar',
  component: Avatar,
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['xs', 'sm', 'md', 'lg', 'xl'],
    },
    status: {
      control: { type: 'select' },
      options: ['online', 'offline', 'away'],
    },
    tooltip: { control: 'boolean' },
  },
};

const Template = (args) => <Avatar {...args} />;

export const Initials = Template.bind({});
Initials.args = {
  name: 'Helly Parmar',
  size: 'md',
  status: 'online',
};

export const Image = Template.bind({});
Image.args = {
  src: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
  name: 'Sarah Jenkins',
  size: 'lg',
  status: 'online',
};

export const Offline = Template.bind({});
Offline.args = {
  name: 'John Doe',
  size: 'md',
  status: 'offline',
};
