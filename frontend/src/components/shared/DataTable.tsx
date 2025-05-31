import React, { useState, useMemo, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { 
  ChevronLeft, 
  ChevronRight, 
  ChevronsLeft, 
  ChevronsRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Filter,
  Download
} from 'lucide-react';

export interface ColumnDefinition<T> {
  key: string;
  header: string;
  accessor: (item: T) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  filterType?: 'text' | 'select' | 'multiselect';
  filterOptions?: Array<{ value: string; label: string }>;
  width?: string;
  align?: 'left' | 'center' | 'right';
  searchableFields?: (keyof T)[];
  resizable?: boolean;
  minWidth?: number;
  maxWidth?: number;
  // Function to extract sortable value from the data item
  sortValue?: (item: T) => string | number;
}

export interface DataTableProps<T> {
  data: T[];
  columns: ColumnDefinition<T>[];
  title?: string;
  searchable?: boolean;
  searchPlaceholder?: string;
  filterable?: boolean;
  selectable?: boolean;
  pagination?: boolean;
  pageSize?: number;
  exportable?: boolean;
  onExport?: (selectedData: T[]) => void;
  onRowClick?: (item: T) => void;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

type SortDirection = 'asc' | 'desc' | null;

interface SortConfig {
  key: string;
  direction: SortDirection;
}

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  title,
  searchable = true,
  searchPlaceholder = "Search...",
  filterable = true,
  selectable = false,
  pagination = true,
  pageSize = 10,
  exportable = false,
  onExport,
  onRowClick,
  loading = false,
  emptyMessage = "No data available",
  className = ""
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: '', direction: null });
  const [columnFilters, setColumnFilters] = useState<Record<string, any>>({});
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [isResizing, setIsResizing] = useState<string | null>(null);

  // Helper function to recursively search in objects
  const searchInObject = useCallback((obj: any, query: string): boolean => {
    if (obj === null || obj === undefined) return false;
    
    if (typeof obj === 'string') {
      return obj.toLowerCase().includes(query);
    }
    
    if (typeof obj === 'number' || typeof obj === 'boolean') {
      return obj.toString().toLowerCase().includes(query);
    }
    
    if (Array.isArray(obj)) {
      return obj.some(item => searchInObject(item, query));
    }
    
    if (typeof obj === 'object') {
      // Common searchable properties in GCP entities
      const commonSearchableProps = [
        'name', 'id', 'email', 'type', 'source', 'target', 
        'project_id', 'projectId', 'displayName', 'description',
        'role', 'permission', 'resource', 'technique', 'via_role',
        'title', 'state', 'location', 'zone', 'region'
      ];
      
      return Object.entries(obj).some(([key, value]) => {
        // Search in common searchable properties
        if (commonSearchableProps.includes(key.toLowerCase())) {
          return searchInObject(value, query);
        }
        
        // Also search in keys that might be relevant
        if (key.toLowerCase().includes(query)) {
          return true;
        }
        
        // Recursively search in nested objects for smaller objects (avoid deep recursion)
        if (typeof value === 'object' && value !== null && Object.keys(value).length < 10) {
          return searchInObject(value, query);
        }
        
        return false;
      });
    }
    
    return false;
  }, []);

  // Filter and search data
  const filteredData = useMemo(() => {
    let result = data;

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      
      result = result.filter((item) => {
        // Search through all searchable fields defined in columns
        const columnSearchMatch = columns.some((column) => {
          if (column.searchableFields && column.searchableFields.length > 0) {
            return column.searchableFields.some(field => {
              const value = item[field];
              if (value === null || value === undefined) return false;
              
              // Handle different types of values
              if (typeof value === 'string') {
                return value.toLowerCase().includes(query);
              }
              
              if (typeof value === 'object' && value !== null) {
                // Search through nested object properties
                return searchInObject(value, query);
              }
              
              return value.toString().toLowerCase().includes(query);
            });
          }
          return false;
        });

        if (columnSearchMatch) return true;

        // Fallback: search through common properties if no specific searchable fields are defined
        return searchInObject(item, query);
      });
    }

    // Apply column filters
    Object.entries(columnFilters).forEach(([columnKey, filterValue]) => {
      if (filterValue && filterValue !== '' && filterValue.length > 0) {
        const column = columns.find(col => col.key === columnKey);
        if (column) {
          result = result.filter((item) => {
            // For filtering, we need to use the raw data value
            const value = item[columnKey]?.toString() || '';
            
            if (Array.isArray(filterValue)) {
              return filterValue.some(fv => value.toLowerCase().includes(fv.toLowerCase()));
            } else {
              return value.toLowerCase().includes(filterValue.toLowerCase());
            }
          });
        }
      }
    });

    return result;
  }, [data, searchQuery, columnFilters, columns]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) {
      return filteredData;
    }

    const column = columns.find(col => col.key === sortConfig.key);
    if (!column) return filteredData;

    return [...filteredData].sort((a, b) => {
      let aValue: string | number;
      let bValue: string | number;

      if (column.sortValue) {
        // Use the custom sort value function if provided
        aValue = column.sortValue(a);
        bValue = column.sortValue(b);
      } else {
        // Fall back to using the raw data value by column key
        aValue = a[column.key] || '';
        bValue = b[column.key] || '';
      }

      // Convert to strings for comparison if they're not numbers
      const aStr = typeof aValue === 'number' ? aValue : aValue.toString().toLowerCase();
      const bStr = typeof bValue === 'number' ? bValue : bValue.toString().toLowerCase();

      // Handle numeric vs string comparison
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      } else {
        // String comparison
        const aCompare = aStr.toString();
        const bCompare = bStr.toString();
        if (sortConfig.direction === 'asc') {
          return aCompare.localeCompare(bCompare);
        } else {
          return bCompare.localeCompare(aCompare);
        }
      }
    });
  }, [filteredData, sortConfig, columns]);

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;
    
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, currentPage, pageSize, pagination]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleSort = (columnKey: string) => {
    const column = columns.find(col => col.key === columnKey);
    if (!column?.sortable) return;

    setSortConfig(prev => {
      if (prev.key === columnKey) {
        if (prev.direction === 'asc') return { key: columnKey, direction: 'desc' };
        if (prev.direction === 'desc') return { key: '', direction: null };
      }
      return { key: columnKey, direction: 'asc' };
    });
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedRows(new Set(paginatedData.map((_, index) => index)));
    } else {
      setSelectedRows(new Set());
    }
  };

  const handleSelectRow = (index: number, checked: boolean) => {
    const newSelected = new Set(selectedRows);
    if (checked) {
      newSelected.add(index);
    } else {
      newSelected.delete(index);
    }
    setSelectedRows(newSelected);
  };

  const handleExport = () => {
    if (!onExport) return;
    
    const selectedData = selectable && selectedRows.size > 0
      ? paginatedData.filter((_, index) => selectedRows.has(index))
      : sortedData; // Export all filtered/sorted data when nothing is selected
    
    onExport(selectedData);
  };

  const getSortIcon = (columnKey: string) => {
    if (sortConfig.key !== columnKey) return <ArrowUpDown className="h-4 w-4" />;
    if (sortConfig.direction === 'asc') return <ArrowUp className="h-4 w-4" />;
    if (sortConfig.direction === 'desc') return <ArrowDown className="h-4 w-4" />;
    return <ArrowUpDown className="h-4 w-4" />;
  };

  const renderColumnFilter = (column: ColumnDefinition<T>) => {
    if (!column.filterable) return null;

    const currentValue = columnFilters[column.key] || '';

    if (column.filterType === 'select' && column.filterOptions) {
      return (
        <Select
          value={currentValue || '__all__'}
          onValueChange={(value) => 
            setColumnFilters(prev => ({ ...prev, [column.key]: value === '__all__' ? '' : value }))
          }
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder={`Filter ${column.header.toLowerCase()}`} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All</SelectItem>
            {column.filterOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }

    return (
      <Input
        placeholder={`Filter ${column.header.toLowerCase()}...`}
        value={currentValue}
        onChange={(e) => 
          setColumnFilters(prev => ({ ...prev, [column.key]: e.target.value }))
        }
        className="w-full"
      />
    );
  };

  // Column resize functionality
  const handleMouseDown = useCallback((columnKey: string, e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(columnKey);
    
    const startX = e.clientX;
    const column = columns.find(col => col.key === columnKey);
    const startWidth = columnWidths[columnKey] || (column?.minWidth || 150);
    
    const handleMouseMove = (e: MouseEvent) => {
      const diff = e.clientX - startX;
      const newWidth = Math.max(
        column?.minWidth || 100,
        Math.min(column?.maxWidth || 500, startWidth + diff)
      );
      
      setColumnWidths(prev => ({
        ...prev,
        [columnKey]: newWidth
      }));
    };
    
    const handleMouseUp = () => {
      setIsResizing(null);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [columns, columnWidths]);

  // Get column width
  const getColumnWidth = useCallback((column: ColumnDefinition<T>) => {
    if (columnWidths[column.key]) {
      return `${columnWidths[column.key]}px`;
    }
    return column.width || 'auto';
  }, [columnWidths]);

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2 text-muted-foreground">Loading...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      {title && (
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{title}</span>
            <div className="flex items-center space-x-2">
              {filterable && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsFilterOpen(!isFilterOpen)}
                >
                  <Filter className="h-4 w-4 mr-2" />
                  Filters
                </Button>
              )}
              {exportable && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExport}
                >
                  <Download className="h-4 w-4 mr-2" />
                  {selectable && selectedRows.size > 0 
                    ? `Export Selected (${selectedRows.size})`
                    : `Export All (${sortedData.length})`
                  }
                </Button>
              )}
            </div>
          </CardTitle>
        </CardHeader>
      )}
      
      <CardContent>
        {/* Search and filter controls */}
        <div className="space-y-4 mb-6">
          {searchable && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          )}

          {/* Column filters */}
          {filterable && isFilterOpen && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4 border rounded-lg bg-muted/50">
              {columns
                .filter(col => col.filterable)
                .map((column) => (
                  <div key={column.key}>
                    <label className="text-sm font-medium mb-2 block">
                      {column.header}
                    </label>
                    {renderColumnFilter(column)}
                  </div>
                ))}
            </div>
          )}
        </div>

        {/* Data display info */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted-foreground">
            Showing {paginatedData.length} of {sortedData.length} results
            {selectable && selectedRows.size > 0 && (
              <span className="ml-2">({selectedRows.size} selected)</span>
            )}
          </p>
          {pagination && totalPages > 1 && (
            <p className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </p>
          )}
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {selectable && (
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedRows.size === paginatedData.length && paginatedData.length > 0}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                )}
                {columns.map((column) => (
                  <TableHead
                    key={column.key}
                    className={`${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : ''} relative`}
                    style={{ 
                      width: getColumnWidth(column),
                      minWidth: column.minWidth || 100,
                      maxWidth: column.maxWidth || 500
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        {column.sortable ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-auto p-0 font-semibold"
                            onClick={() => handleSort(column.key)}
                          >
                            {column.header}
                            <span className="ml-2">
                              {getSortIcon(column.key)}
                            </span>
                          </Button>
                        ) : (
                          <span className="font-semibold">{column.header}</span>
                        )}
                      </div>
                      
                      {/* Resize handle */}
                      {column.resizable && (
                        <div
                          className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-border transition-colors group"
                          onMouseDown={(e) => handleMouseDown(column.key, e)}
                          title="Drag to resize column"
                        >
                          <div className="h-full w-full group-hover:bg-blue-500/20" />
                        </div>
                      )}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.length === 0 ? (
                <TableRow>
                  <TableCell 
                    colSpan={columns.length + (selectable ? 1 : 0)} 
                    className="text-center py-8 text-muted-foreground"
                  >
                    {emptyMessage}
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((item, index) => (
                  <TableRow
                    key={index}
                    className={`${onRowClick ? 'cursor-pointer hover:bg-muted/50' : ''}`}
                    onClick={() => onRowClick?.(item)}
                  >
                    {selectable && (
                      <TableCell>
                        <Checkbox
                          checked={selectedRows.has(index)}
                          onCheckedChange={(checked) => handleSelectRow(index, checked as boolean)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </TableCell>
                    )}
                    {columns.map((column) => (
                      <TableCell
                        key={column.key}
                        className={`${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : ''}`}
                        style={{ 
                          width: getColumnWidth(column),
                          minWidth: column.minWidth || 100,
                          maxWidth: column.maxWidth || 500
                        }}
                      >
                        {column.accessor(item)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {pagination && totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>

            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}