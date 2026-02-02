import React from 'react';
import { Search } from 'lucide-react';

/**
 * SearchInput Component
 * Standardized search input with consistent styling across the application
 * WCAG AA compliant with proper contrast and focus states
 */
const SearchInput = ({
    placeholder = "Search...",
    value,
    onChange,
    onSearch,
    className = "",
    containerClassName = "",
    size = "md" // sm, md, lg
}) => {
    const sizeClasses = {
        sm: "py-2 text-sm",
        md: "py-2.5 text-base",
        lg: "py-3 text-lg"
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && onSearch) {
            onSearch(value);
        }
    };

    return (
        <div className={`relative flex-1 max-w-md ${containerClassName}`}>
            <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
                size={20}
            />
            <input
                type="text"
                value={value}
                onChange={onChange}
                onKeyPress={handleKeyPress}
                placeholder={placeholder}
                className={`
                    w-full pl-10 pr-4 ${sizeClasses[size]}
                    bg-card border-2 border-border rounded-lg 
                    text-foreground placeholder:text-muted-foreground
                    focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent
                    transition-all duration-200
                    ${className}
                `}
                aria-label={placeholder}
            />
        </div>
    );
};

export default SearchInput;
