package com.fantaco.finance.entity;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.*;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "orders")
@Schema(description = "Order entity representing a customer order")
public class Order {
    
    @Schema(description = "Unique identifier for the order", example = "1")
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Schema(description = "Unique order number", example = "ORD-2024-001")
    @NotBlank
    @Column(name = "order_number", unique = true, nullable = false)
    private String orderNumber;
    
    @Schema(description = "Customer identifier", example = "CUST-12345")
    @NotBlank
    @Column(name = "customer_id", nullable = false)
    private String customerId;
    
    @Schema(description = "Total amount for the order", example = "99.99")
    @NotNull
    @DecimalMin(value = "0.0", inclusive = false)
    @Column(name = "total_amount", nullable = false, precision = 10, scale = 2)
    private BigDecimal totalAmount;
    
    @Schema(description = "Current status of the order", example = "CONFIRMED")
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private OrderStatus status;
    
    @Schema(description = "Date when the order was placed", example = "2024-01-15T10:30:00")
    @Column(name = "order_date", nullable = false)
    private LocalDateTime orderDate;
    
    @Schema(description = "Timestamp when the record was created", example = "2024-01-15T10:30:00")
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
    
    @Schema(description = "Timestamp when the record was last updated", example = "2024-01-15T11:00:00")
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Constructors
    public Order() {
        this.createdAt = LocalDateTime.now();
    }
    
    public Order(String orderNumber, String customerId, BigDecimal totalAmount, OrderStatus status) {
        this();
        this.orderNumber = orderNumber;
        this.customerId = customerId;
        this.totalAmount = totalAmount;
        this.status = status;
        this.orderDate = LocalDateTime.now();
    }
    
    // Getters and Setters
    public Long getId() {
        return id;
    }
    
    public void setId(Long id) {
        this.id = id;
    }
    
    public String getOrderNumber() {
        return orderNumber;
    }
    
    public void setOrderNumber(String orderNumber) {
        this.orderNumber = orderNumber;
    }
    
    public String getCustomerId() {
        return customerId;
    }
    
    public void setCustomerId(String customerId) {
        this.customerId = customerId;
    }
    
    public BigDecimal getTotalAmount() {
        return totalAmount;
    }
    
    public void setTotalAmount(BigDecimal totalAmount) {
        this.totalAmount = totalAmount;
    }
    
    public OrderStatus getStatus() {
        return status;
    }
    
    public void setStatus(OrderStatus status) {
        this.status = status;
    }
    
    public LocalDateTime getOrderDate() {
        return orderDate;
    }
    
    public void setOrderDate(LocalDateTime orderDate) {
        this.orderDate = orderDate;
    }
    
    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
    
    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
    
    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
    
    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
    
    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
    
    @Schema(description = "Order status enumeration")
    public enum OrderStatus {
        @Schema(description = "Order is pending confirmation")
        PENDING, 
        @Schema(description = "Order has been confirmed")
        CONFIRMED, 
        @Schema(description = "Order has been shipped")
        SHIPPED, 
        @Schema(description = "Order has been delivered")
        DELIVERED, 
        @Schema(description = "Order has been cancelled")
        CANCELLED, 
        @Schema(description = "Order has been refunded")
        REFUNDED
    }
}
