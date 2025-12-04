-- Sample data for Fantaco Finance API

-- Insert sample orders
INSERT INTO orders (order_number, customer_id, total_amount, status, order_date, created_at) VALUES
('ORD-001', 'LONEP', 299.99, 'DELIVERED', '2024-01-15 10:30:00', '2024-01-15 10:30:00'),
('ORD-002', 'LONEP', 149.50, 'SHIPPED', '2024-01-20 14:15:00', '2024-01-20 14:15:00'),
('ORD-003', 'AROUT', 89.99, 'PENDING', '2024-01-25 09:45:00', '2024-01-25 09:45:00'),
('ORD-004', 'AROUT', 199.99, 'DELIVERED', '2024-01-10 16:20:00', '2024-01-10 16:20:00'),
('ORD-005', 'THECR', 79.99, 'CANCELLED', '2024-01-22 11:10:00', '2024-01-22 11:10:00'),
('ORD-006', 'LONEP', 399.99, 'DELIVERED', '2024-01-05 08:30:00', '2024-01-05 08:30:00'),
('ORD-007', 'THECR', 129.99, 'SHIPPED', '2024-01-28 13:45:00', '2024-01-28 13:45:00'),
('ORD-008', 'AROUT', 59.99, 'PENDING', '2024-01-30 15:20:00', '2024-01-30 15:20:00');

-- Insert sample invoices
INSERT INTO invoices (invoice_number, order_id, customer_id, amount, status, invoice_date, due_date, paid_date, created_at) VALUES
('INV-001', 1, 'LONEP', 299.99, 'PAID', '2024-01-15 10:35:00', '2024-02-15 10:35:00', '2024-01-16 09:20:00', '2024-01-15 10:35:00'),
('INV-002', 2, 'LONEP', 149.50, 'SENT', '2024-01-20 14:20:00', '2024-02-20 14:20:00', NULL, '2024-01-20 14:20:00'),
('INV-003', 3, 'AROUT', 89.99, 'DRAFT', '2024-01-25 09:50:00', '2024-02-25 09:50:00', NULL, '2024-01-25 09:50:00'),
('INV-004', 4, 'AROUT', 199.99, 'PAID', '2024-01-10 16:25:00', '2024-02-10 16:25:00', '2024-01-12 14:30:00', '2024-01-10 16:25:00'),
('INV-005', 5, 'THECR', 79.99, 'CANCELLED', '2024-01-22 11:15:00', '2024-02-22 11:15:00', NULL, '2024-01-22 11:15:00'),
('INV-006', 6, 'LONEP', 399.99, 'PAID', '2024-01-05 08:35:00', '2024-02-05 08:35:00', '2024-01-07 10:15:00', '2024-01-05 08:35:00'),
('INV-007', 7, 'THECR', 129.99, 'SENT', '2024-01-28 13:50:00', '2024-02-28 13:50:00', NULL, '2024-01-28 13:50:00'),
('INV-008', 8, 'AROUT', 59.99, 'DRAFT', '2024-01-30 15:25:00', '2024-02-28 15:25:00', NULL, '2024-01-30 15:25:00');

-- Insert sample disputes
INSERT INTO disputes (dispute_number, order_id, customer_id, dispute_type, status, description, reason, dispute_date, created_at) VALUES
('DISP-001', 1, 'LONEP', 'BILLING_ERROR', 'RESOLVED', 'Incorrect tax calculation on invoice', 'Tax rate was applied incorrectly', '2024-01-18 10:00:00', '2024-01-18 10:00:00'),
('DISP-002', 2, 'LONEP', 'DUPLICATE_CHARGE', 'OPEN', 'Charged twice for the same order', 'Payment processor error caused duplicate charge', '2024-01-22 14:30:00', '2024-01-22 14:30:00'),
('DISP-003', 4, 'AROUT', 'PRODUCT_NOT_RECEIVED', 'IN_PROGRESS', 'Order marked as delivered but never received', 'Package may have been stolen or misdelivered', '2024-01-15 16:45:00', '2024-01-15 16:45:00');

-- Insert sample receipts
INSERT INTO receipts (receipt_number, order_id, customer_id, status, file_path, file_name, file_size, mime_type, receipt_date, created_at) VALUES
('RCPT-001', 1, 'LONEP', 'FOUND', '/receipts/2024/01/rcpt-001.pdf', 'receipt-001.pdf', 245760, 'application/pdf', '2024-01-15 10:40:00', '2024-01-15 10:40:00'),
('RCPT-002', 2, 'LONEP', 'PENDING', NULL, NULL, NULL, NULL, '2024-01-20 14:25:00', '2024-01-20 14:25:00'),
('RCPT-003', 3, 'AROUT', 'LOST', NULL, NULL, NULL, NULL, '2024-01-25 09:55:00', '2024-01-25 09:55:00'),
('RCPT-004', 4, 'AROUT', 'FOUND', '/receipts/2024/01/rcpt-004.pdf', 'receipt-004.pdf', 198432, 'application/pdf', '2024-01-10 16:30:00', '2024-01-10 16:30:00'),
('RCPT-005', 5, 'THECR', 'CANCELLED', NULL, NULL, NULL, NULL, '2024-01-22 11:20:00', '2024-01-22 11:20:00'),
('RCPT-006', 6, 'LONEP', 'FOUND', '/receipts/2024/01/rcpt-006.pdf', 'receipt-006.pdf', 312456, 'application/pdf', '2024-01-05 08:40:00', '2024-01-05 08:40:00'),
('RCPT-007', 7, 'THECR', 'PENDING', NULL, NULL, NULL, NULL, '2024-01-28 13:55:00', '2024-01-28 13:55:00'),
('RCPT-008', 8, 'AROUT', 'LOST', NULL, NULL, NULL, NULL, '2024-01-30 15:30:00', '2024-01-30 15:30:00');
