/**
 * Loading Notice Component
 * Simple loading indicator to replace skeleton loaders
 */

import { Loader2 } from 'lucide-react';

const LoadingNotice = ({ message = "Loading..." }) => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
            <Loader2 className="w-12 h-12 text-primary animate-spin" />
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                {message}
            </p>
        </div>
    );
};

export default LoadingNotice;
