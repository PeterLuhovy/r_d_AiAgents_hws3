-- Initialize database for invoice management
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date_created DATE NOT NULL,
    due_date DATE NOT NULL
);

-- Create index for faster queries
CREATE INDEX idx_invoices_date_created ON invoices(date_created);
CREATE INDEX idx_invoices_supplier ON invoices(supplier_name);