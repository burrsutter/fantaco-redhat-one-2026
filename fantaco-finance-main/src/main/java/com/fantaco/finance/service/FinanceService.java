package com.fantaco.finance.service;

import com.fantaco.finance.dto.*;
import com.fantaco.finance.entity.*;
import com.fantaco.finance.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@Transactional
public class FinanceService {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private InvoiceRepository invoiceRepository;
    
    @Autowired
    private DisputeRepository disputeRepository;
    
    @Autowired
    private ReceiptRepository receiptRepository;
    
    /**
     * Get order history for a customer
     */
    public List<Order> getOrderHistory(OrderHistoryRequest request) {
        if (request.getStartDate() != null && request.getEndDate() != null) {
            return orderRepository.findByCustomerIdAndOrderDateBetweenOrderByOrderDateDesc(
                    request.getCustomerId(), request.getStartDate(), request.getEndDate());
        } else if (request.getStartDate() != null) {
            return orderRepository.findRecentOrdersByCustomer(
                    request.getCustomerId(), request.getStartDate());
        } else {
            List<Order> orders = orderRepository.findByCustomerIdOrderByOrderDateDesc(request.getCustomerId());
            return orders.stream()
                    .limit(request.getLimit())
                    .toList();
        }
    }
    
    /**
     * Get invoice history for a customer
     */
    public List<Invoice> getInvoiceHistory(InvoiceHistoryRequest request) {
        if (request.getStartDate() != null && request.getEndDate() != null) {
            return invoiceRepository.findByCustomerIdAndInvoiceDateBetweenOrderByInvoiceDateDesc(
                    request.getCustomerId(), request.getStartDate(), request.getEndDate());
        } else if (request.getStartDate() != null) {
            return invoiceRepository.findRecentInvoicesByCustomer(
                    request.getCustomerId(), request.getStartDate());
        } else {
            List<Invoice> invoices = invoiceRepository.findByCustomerIdOrderByInvoiceDateDesc(request.getCustomerId());
            return invoices.stream()
                    .limit(request.getLimit())
                    .toList();
        }
    }
    
    /**
     * Start a duplicate charge dispute
     */
    public Dispute startDuplicateChargeDispute(DuplicateChargeDisputeRequest request) {
        // Check if order exists
        Order order = orderRepository.findById(request.getOrderId())
                .orElseThrow(() -> new RuntimeException("Order not found with ID: " + request.getOrderId()));
        
        // Check if customer owns the order
        if (!order.getCustomerId().equals(request.getCustomerId())) {
            throw new RuntimeException("Order does not belong to customer: " + request.getCustomerId());
        }
        
        // Check if there's already an active duplicate charge dispute for this order
        long activeDisputes = disputeRepository.countActiveDisputesByOrderAndType(
                request.getOrderId(), Dispute.DisputeType.DUPLICATE_CHARGE);
        
        if (activeDisputes > 0) {
            throw new RuntimeException("Duplicate charge dispute already exists for order: " + request.getOrderId());
        }
        
        // Create new dispute
        String disputeNumber = "DISP-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        Dispute dispute = new Dispute(
                disputeNumber,
                request.getOrderId(),
                request.getCustomerId(),
                Dispute.DisputeType.DUPLICATE_CHARGE,
                Dispute.DisputeStatus.OPEN
        );
        
        dispute.setDescription(request.getDescription());
        dispute.setReason(request.getReason());
        
        return disputeRepository.save(dispute);
    }
    
    /**
     * Find lost receipt for an order
     */
    public Receipt findLostReceipt(FindLostReceiptRequest request) {
        // Check if order exists
        Order order = orderRepository.findById(request.getOrderId())
                .orElseThrow(() -> new RuntimeException("Order not found with ID: " + request.getOrderId()));
        
        // Check if customer owns the order
        if (!order.getCustomerId().equals(request.getCustomerId())) {
            throw new RuntimeException("Order does not belong to customer: " + request.getCustomerId());
        }
        
        // Check if there's already a lost receipt for this order
        List<Receipt> existingLostReceipts = receiptRepository.findLostReceiptsByOrder(request.getOrderId());
        if (!existingLostReceipts.isEmpty()) {
            return existingLostReceipts.get(0); // Return the first lost receipt
        }
        
        // Create new lost receipt record
        String receiptNumber = "RCPT-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        Receipt receipt = new Receipt(
                receiptNumber,
                request.getOrderId(),
                request.getCustomerId(),
                Receipt.ReceiptStatus.LOST
        );
        
        return receiptRepository.save(receipt);
    }
    
    /**
     * Get all lost receipts for a customer
     */
    public List<Receipt> getLostReceiptsByCustomer(String customerId) {
        return receiptRepository.findLostReceiptsByCustomer(customerId);
    }
    
    /**
     * Get all disputes for a customer
     */
    public List<Dispute> getDisputesByCustomer(String customerId) {
        return disputeRepository.findByCustomerIdOrderByDisputeDateDesc(customerId);
    }
}
