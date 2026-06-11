import React from 'react';
import { Tooltip } from './Tooltip';
import { Button } from './Button';

export default {
  title: 'UI/Tooltip',
  component: Tooltip,
  argTypes: {
    position: {
      control: { type: 'select' },
      options: ['top', 'bottom', 'left', 'right'],
    },
  },
};

const Template = (args) => (
  <div style={{ padding: '60px', display: 'flex', justifyContent: 'center' }}>
    <Tooltip {...args}>
      <Button variant="secondary">Hover Me</Button>
    </Tooltip>
  </div>
);

export const Top = Template.bind({});
Top.args = {
  content: 'This action is irreversible.',
  position: 'top',
};

export const Bottom = Template.bind({});
Bottom.args = {
  content: 'Click to open details panel.',
  position: 'bottom',
};

export const Left = Template.bind({});
Left.args = {
  content: 'Help center documentation.',
  position: 'left',
};

export const Right = Template.bind({});
Right.args = {
  content: 'Save settings changes.',
  position: 'right',
};
