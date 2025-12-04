package com.fantaco.finance.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

@Schema(description = "Request object for starting a duplicate charge dispute")
public class DuplicateChargeDisputeRequest {
    
    @Schema(description = "Unique identifier for the customer", example = "CUST-12345", required = true)
    @NotBlank(message = "Customer ID is required")
    private String customerId;
    
    @Schema(description = "Unique identifier for the order", example = "12345", required = true)
    @NotNull(message = "Order ID is required")
    private Long orderId;
    
    @Schema(description = "Detailed description of the duplicate charge issue", example = "I was charged twice for the same order on 2024-01-15", required = true)
    @NotBlank(message = "Description is required")
    private String description;
    
    @Schema(description = "Optional reason code for the dispute", example = "DUPLICATE_PAYMENT")
    private String reason;
    
    // Constructors
    public DuplicateChargeDisputeRequest() {}
    
    public DuplicateChargeDisputeRequest(String customerId, Long orderId, String description) {
        this.customerId = customerId;
        this.orderId = orderId;
        this.description = description;
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
    
    public String getDescription() {
        return description;
    }
    
    public void setDescription(String description) {
        this.description = description;
    }
    
    public String getReason() {
        return reason;
    }
    
    public void setReason(String reason) {
        this.reason = reason;
    }

    @Override
    public String toString() {
        return "DuplicateChargeDisputeRequest{" +
                "customerId='" + customerId + '\'' +
                ", orderId=" + orderId +
                ", description='" + description + '\'' +
                ", reason='" + reason + '\'' +
                '}';
    }
}
