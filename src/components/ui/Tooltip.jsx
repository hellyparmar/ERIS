import React from 'react';

/**
 * Tooltip Component
 * Accessible tooltip with keyboard support
 */
const Tooltip = ({ children, content, position = 'top' }) => {
    const [isVisible, setIsVisible] = React.useState(false);
    const [isFocused, setIsFocused] = React.useState(false);
    const tooltipId = React.useId();

    const positions = {
        top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
        bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
        left: 'right-full top-1/2 -translate-y-1/2 mr-2',
        right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    };

    const show = isVisible || isFocused;

    return (
        <div
            className="relative inline-block"
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
        >
            <div aria-describedby={show ? tooltipId : undefined}>
                {children}
            </div>

            
                {show && (
                    <div
                        id={tooltipId}
                        role="tooltip"
                        className={`absolute ${positions[position]} z-50 px-3 py-2 text-sm text-white bg-gray-900 dark:bg-gray-700 rounded-lg shadow-lg whitespace-nowrap pointer-events-none`}
                        }
                        }
                    >
                        {content}
                        <div
                            className={`absolute w-2 h-2 bg-gray-900 dark:bg-gray-700 transform rotate-45 ${position === 'top' ? 'bottom-[-4px] left-1/2 -translate-x-1/2' :
                                    position === 'bottom' ? 'top-[-4px] left-1/2 -translate-x-1/2' :
                                        position === 'left' ? 'right-[-4px] top-1/2 -translate-y-1/2' :
                                            'left-[-4px] top-1/2 -translate-y-1/2'
                                }`}
                            aria-hidden="true"
                        />
                    </div>
                )}
            
        </div>
    );
};

export default Tooltip;
