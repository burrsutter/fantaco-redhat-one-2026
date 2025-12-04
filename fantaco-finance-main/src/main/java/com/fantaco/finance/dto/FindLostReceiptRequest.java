package com.fantaco.finance.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

@Schema(description = "Request object for finding or regenerating a lost receipt")
public class FindLostReceiptRequest {
    
    @Schema(description = "Unique identifier for the customer", example = "CUST-12345", required = true)
    @NotBlank(message = "Customer ID is required")
    private String customerId;
    
    @Schema(description = "Unique identifier for the order", example = "12345", required = true)
    @NotNull(message = "Order ID is required")
    private Long orderId;
    
    // Constructors
    public FindLostReceiptRequest() {}
    
    public FindLostReceiptRequest(String customerId, Long orderId) {
        this.customerId = customerId;
        this.orderId = orderId;
    }
    
    // Getters and Setters
    public String getCustomerId() {
        return customerId;
    }
    
    public void setCustomerId(String customerId) {
        this.customerId = customerId;
    }
    
    public Long getOrderId() {
        return orderId;
    }
    
    public void setOrderId(Long orderId) {
        this.orderId = orderId;
    }

    @Override
    public String toString() {
        return "FindLostReceiptRequest{" +
                "customerId='" + customerId + '\'' +
                ", orderId=" + orderId +
                '}';
    }
}
