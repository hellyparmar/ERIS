import { SearchInput as MasterSearchInput } from './index';

export default function SearchInput({ 
  value, 
  onChange, 
  onSearch, 
  placeholder = "Search...", 
  className = "", 
  containerClassName = "",
  onClear
}) {
  const handleChange = (val) => {
    if (onChange) {
      onChange({ target: { value: val } });
    }
  };

  return (
    <MasterSearchInput
      value={value}
      onChange={handleChange}
      onDebouncedSearch={onSearch}
      placeholder={placeholder}
      className={`${containerClassName} ${className}`}
      onClear={onClear}
    />
  );
}

export { MasterSearchInput as SearchInput };
