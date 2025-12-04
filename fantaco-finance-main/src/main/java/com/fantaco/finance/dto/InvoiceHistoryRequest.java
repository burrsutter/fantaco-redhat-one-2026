package com.fantaco.finance.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import java.time.LocalDateTime;

@Schema(description = "Request object for retrieving invoice history for a customer")
public class InvoiceHistoryRequest {
    
    @Schema(description = "Unique identifier for the customer", example = "CUST-12345", required = true)
    @NotBlank(message = "Customer ID is required")
    private String customerId;
    
    @Schema(description = "Start date for filtering invoices (ISO 8601 format)", example = "2024-01-01T00:00:00")
    private LocalDateTime startDate;
    
    @Schema(description = "End date for filtering invoices (ISO 8601 format)", example = "2024-12-31T23:59:59")
    private LocalDateTime endDate;
    
    @Schema(description = "Maximum number of invoices to return", example = "50", defaultValue = "50")
    private Integer limit = 50; // Default limit
    
    // Constructors
    public InvoiceHistoryRequest() {}
    
    public InvoiceHistoryRequest(String customerId) {
        this.customerId = customerId;
    }
    
    public InvoiceHistoryRequest(String customerId, LocalDateTime startDate, LocalDateTime endDate) {
        this.customerId = customerId;
        this.startDate = startDate;
        this.endDate = endDate;
    }
    
    // Getters and Setters
    public String getCustomerId() {
        return customerId;
    }
    
    public void setCustomerId(String customerId) {
        this.customerId = customerId;
    }
    
    public LocalDateTime getStartDate() {
        return startDate;
    }
    
    public void setStartDate(LocalDateTime startDate) {
        this.startDate = startDate;
    }
    
    public LocalDateTime getEndDate() {
        return endDate;
    }
    
    public void setEndDate(LocalDateTime endDate) {
        this.endDate = endDate;
    }
    
    public Integer getLimit() {
        return limit;
    }
    
    public void setLimit(Integer limit) {
        this.limit = limit;
    }

    @Override
    public String toString() {
        return "InvoiceHistoryRequest{" +
                "customerId='" + customerId + '\'' +
                ", startDate=" + startDate +
                ", endDate=" + endDate +
                ", limit=" + limit +
                '}';
    }
}
