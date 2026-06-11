import React, { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';

export default {
  title: 'UI/Modal',
  component: Modal,
  argTypes: {
    layout: {
      control: { type: 'select' },
      options: ['center', 'drawer'],
    },
    open: { control: 'boolean' },
  },
};

const Template = (args) => {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal 
        {...args} 
        open={open} 
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="primary" onClick={() => setOpen(false)}>Confirm Action</Button>
          </>
        }
      >
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0 }}>
          This is the body content of the dialog. You can embed any React nodes, checklists, details, forms, or confirmation statements here.
        </p>
      </Modal>
    </div>
  );
};

export const Center = Template.bind({});
Center.args = {
  title: 'Terminal Setup Warning',
  layout: 'center',
};

export const Drawer = Template.bind({});
Drawer.args = {
  title: 'Filter Configurations',
  layout: 'drawer',
};
