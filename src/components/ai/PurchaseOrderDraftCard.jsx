import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ShoppingCart, Calendar, Building, Check, X, Edit2 } from 'lucide-react';

const PurchaseOrderDraftCard = ({ actionData, onConfirm, onCancel }) => {
    const { item, quantity, vendor, delivery_date } = actionData?.data || {};
    const [status, setStatus] = useState('draft'); // draft, confirmed, cancelled

    const handleConfirm = () => {
        setStatus('confirmed');
        // Simulate API call
        setTimeout(() => {
            onConfirm && onConfirm();
        }, 1000);
    };

    const handleCancel = () => {
        setStatus('cancelled');
        onCancel && onCancel();
    };

    if (status === 'confirmed') {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 flex items-center justify-center gap-3 text-green-700 dark:text-green-400"
            >
                <div className="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-full flex items-center justify-center">
                    <Check className="w-5 h-5" />
                </div>
                <span className="font-medium">Purchase Order Created Successfully</span>
            </motion.div>
        );
    }

    if (status === 'cancelled') {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-center justify-center gap-3 text-red-700 dark:text-red-400"
            >
                <div className="w-8 h-8 bg-red-100 dark:bg-red-800 rounded-full flex items-center justify-center">
                    <X className="w-5 h-5" />
                </div>
                <span className="font-medium">Draft Cancelled</span>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-md bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border border-purple-200 dark:border-purple-500/30 rounded-xl overflow-hidden shadow-lg my-2"
        >
            <div className="bg-gradient-to-r from-purple-500 to-indigo-600 px-4 py-3 flex items-center justify-between">
                <h3 className="text-white font-semibold flex items-center gap-2">
                    <Edit2 className="w-4 h-4" />
                    Draft Purchase Order
                </h3>
                <span className="text-xs bg-white/20 text-white px-2 py-0.5 rounded-full">
                    #DRAFT-001
                </span>
            </div>

            <div className="p-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                            <ShoppingCart className="w-3 h-3" /> Item
                        </label>
                        <p className="font-medium text-gray-900 dark:text-white truncate" title={item}>
                            {item || 'N/A'}
                        </p>
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400">
                            Quantity
                        </label>
                        <p className="font-medium text-gray-900 dark:text-white">
                            {quantity || 0} units
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                            <Building className="w-3 h-3" /> Vendor
                        </label>
                        <p className="font-medium text-gray-900 dark:text-white truncate" title={vendor}>
                            {vendor || 'Unknown Vendor'}
                        </p>
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                            <Calendar className="w-3 h-3" /> Expected Delivery
                        </label>
                        <p className="font-medium text-gray-900 dark:text-white">
                            {delivery_date || 'ASAP'}
                        </p>
                    </div>
                </div>

                {/* Mock Estimated Cost */}
                <div className="bg-purple-50 dark:bg-purple-900/10 rounded-lg p-3 flex justify-between items-center">
                    <span className="text-sm text-purple-700 dark:text-purple-300">Estimated Cost</span>
                    <span className="text-lg font-bold text-purple-700 dark:text-purple-300">
                        ${(quantity * 10).toLocaleString()} (est)
                    </span>
                </div>

                <div className="flex gap-3 pt-2">
                    <button
                        onClick={handleCancel}
                        className="flex-1 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        className="flex-1 px-4 py-2 text-sm font-bold tracking-wide !text-white bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg hover:from-purple-700 hover:to-indigo-700 shadow-md transition-all flex items-center justify-center gap-2"
                    >
                        Confirm Order
                    </button>
                </div>
            </div>
        </motion.div>
    );
};

export default PurchaseOrderDraftCard;
