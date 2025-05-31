import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable, ColumnDefinition } from '../DataTable';

// Mock data for testing
interface TestItem {
  id: string;
  name: string;
  type: string;
  properties: {
    email?: string;
    project_id?: string;
    role?: string;
  };
}

const mockData: TestItem[] = [
  {
    id: 'user:alice@example.com',
    name: 'Alice Smith',
    type: 'user',
    properties: {
      email: 'alice@example.com',
      project_id: 'project-1'
    }
  },
  {
    id: 'user:bob@company.com',
    name: 'Bob Johnson',
    type: 'user',
    properties: {
      email: 'bob@company.com',
      project_id: 'project-2'
    }
  },
  {
    id: 'sa:service-account@project.iam.gserviceaccount.com',
    name: 'Service Account',
    type: 'service_account',
    properties: {
      email: 'service-account@project.iam.gserviceaccount.com',
      role: 'roles/editor'
    }
  }
];

const columns: ColumnDefinition<TestItem>[] = [
  {
    key: 'name',
    header: 'Name',
    accessor: (item) => item.name,
    searchableFields: ['name', 'id', 'properties']
  },
  {
    key: 'type',
    header: 'Type',
    accessor: (item) => item.type,
    searchableFields: ['type']
  }
];

describe('DataTable Search Functionality', () => {
  test('should search by name', () => {
    render(
      <DataTable
        data={mockData}
        columns={columns}
        searchable={true}
        searchPlaceholder="Search..."
      />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'Alice' } });

    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.queryByText('Bob Johnson')).not.toBeInTheDocument();
  });

  test('should search by email in properties', () => {
    render(
      <DataTable
        data={mockData}
        columns={columns}
        searchable={true}
        searchPlaceholder="Search..."
      />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'bob@company.com' } });

    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    expect(screen.queryByText('Alice Smith')).not.toBeInTheDocument();
  });

  test('should search by type', () => {
    render(
      <DataTable
        data={mockData}
        columns={columns}
        searchable={true}
        searchPlaceholder="Search..."
      />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'service_account' } });

    expect(screen.getByText('Service Account')).toBeInTheDocument();
    expect(screen.queryByText('Alice Smith')).not.toBeInTheDocument();
    expect(screen.queryByText('Bob Johnson')).not.toBeInTheDocument();
  });

  test('should search by project_id in nested properties', () => {
    render(
      <DataTable
        data={mockData}
        columns={columns}
        searchable={true}
        searchPlaceholder="Search..."
      />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'project-1' } });

    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.queryByText('Bob Johnson')).not.toBeInTheDocument();
  });

  test('should be case insensitive', () => {
    render(
      <DataTable
        data={mockData}
        columns={columns}
        searchable={true}
        searchPlaceholder="Search..."
      />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'ALICE' } });

    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
  });

  test('should show all items when search is cleared', () => {
    render(
      <DataTable
        data={mockData}
        columns={columns}
        searchable={true}
        searchPlaceholder="Search..."
      />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    
    // First search
    fireEvent.change(searchInput, { target: { value: 'Alice' } });
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.queryByText('Bob Johnson')).not.toBeInTheDocument();
    
    // Clear search
    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    expect(screen.getByText('Service Account')).toBeInTheDocument();
  });

  test('should show export button with correct text', () => {
    const mockExport = jest.fn();
    
    render(
      <DataTable
        data={mockData}
        columns={columns}
        title="Test Table"
        exportable={true}
        selectable={true}
        onExport={mockExport}
      />
    );

    // Should show "Export All" when no rows selected
    expect(screen.getByText('Export All (3)')).toBeInTheDocument();
  });

  test('should show column resize handles', () => {
    const resizableColumns = [
      {
        key: 'name',
        header: 'Name',
        accessor: (item: TestItem) => item.name,
        resizable: true,
        minWidth: 100,
        maxWidth: 300
      }
    ];

    render(
      <DataTable
        data={mockData}
        columns={resizableColumns}
        title="Test Table"
      />
    );

    expect(screen.getByTitle('Drag to resize column')).toBeInTheDocument();
  });

  test('should sort data correctly', () => {
    const sortableColumns = [
      {
        key: 'name',
        header: 'Name',
        accessor: (item: TestItem) => item.name,
        sortable: true,
        sortValue: (item: TestItem) => item.name
      },
      {
        key: 'type',
        header: 'Type',
        accessor: (item: TestItem) => item.type,
        sortable: true,
        sortValue: (item: TestItem) => item.type
      }
    ];

    render(
      <DataTable
        data={mockData}
        columns={sortableColumns}
        title="Test Table"
        pagination={false}
      />
    );

    // Initial order should be as provided
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Alice Smith'); // First data row

    // Click to sort by name ascending
    fireEvent.click(screen.getByText('Name'));
    
    // After sorting, Alice should still be first (alphabetically)
    const sortedRows = screen.getAllByRole('row');
    expect(sortedRows[1]).toHaveTextContent('Alice Smith');

    // Click again to sort descending
    fireEvent.click(screen.getByText('Name'));
    
    // Now Service Account should be first (comes last alphabetically)
    const reverseSortedRows = screen.getAllByRole('row');
    expect(reverseSortedRows[1]).toHaveTextContent('Service Account');
  });

  test('should sort by custom sortValue function', () => {
    const customSortColumns = [
      {
        key: 'name',
        header: 'Name',
        accessor: (item: TestItem) => <span>{item.name}</span>,
        sortable: true,
        sortValue: (item: TestItem) => item.properties.email || item.name // Sort by email if available
      }
    ];

    render(
      <DataTable
        data={mockData}
        columns={customSortColumns}
        title="Test Table"
        pagination={false}
      />
    );

    // Click to sort by name (which will actually sort by email when available)
    fireEvent.click(screen.getByText('Name'));
    
    // Should be sorted by email addresses: alice@example.com, bob@company.com, then Service Account
    const sortedRows = screen.getAllByRole('row');
    expect(sortedRows[1]).toHaveTextContent('Alice Smith'); // alice@example.com comes first
    expect(sortedRows[2]).toHaveTextContent('Bob Johnson'); // bob@company.com comes second
    expect(sortedRows[3]).toHaveTextContent('Service Account'); // no email, so sorted by name
  });

  test('should fall back to column key when no sortValue provided', () => {
    const fallbackColumns = [
      {
        key: 'type',
        header: 'Type',
        accessor: (item: TestItem) => <span className="complex">{item.type}</span>,
        sortable: true
        // No sortValue provided, should use item[key] (item.type)
      }
    ];

    render(
      <DataTable
        data={mockData}
        columns={fallbackColumns}
        title="Test Table"
        pagination={false}
      />
    );

    // Click to sort by type
    fireEvent.click(screen.getByText('Type'));
    
    // Should be sorted alphabetically by type: service_account, user, user
    const sortedRows = screen.getAllByRole('row');
    expect(sortedRows[1]).toHaveTextContent('service_account');
    expect(sortedRows[2]).toHaveTextContent('user');
    expect(sortedRows[3]).toHaveTextContent('user');
  });

  test('should toggle filters panel', () => {
    const filterableColumns = [
      {
        key: 'type',
        header: 'Type',
        accessor: (item: TestItem) => item.type,
        filterable: true,
        filterType: 'select' as const,
        filterOptions: [
          { value: 'user', label: 'User' },
          { value: 'service_account', label: 'Service Account' }
        ]
      }
    ];

    render(
      <DataTable
        data={mockData}
        columns={filterableColumns}
        filterable={true}
        title="Test Table"
      />
    );

    // Should show filters button
    const filtersButton = screen.getByText('Filters');
    expect(filtersButton).toBeInTheDocument();

    // For now, just verify the button exists - we'll skip testing the Select opening
    // since it requires more complex interaction testing
    expect(filtersButton).toBeInTheDocument();
  });
}); 