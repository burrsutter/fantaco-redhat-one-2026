package com.fantaco.finance.repository;

import com.fantaco.finance.entity.Receipt;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface ReceiptRepository extends JpaRepository<Receipt, Long> {
    
    List<Receipt> findByCustomerIdOrderByReceiptDateDesc(String customerId);
    
    List<Receipt> findByOrderIdOrderByReceiptDateDesc(Long orderId);
    
    List<Receipt> findByStatusOrderByReceiptDateDesc(Receipt.ReceiptStatus status);
    
    Optional<Receipt> findByReceiptNumber(String receiptNumber);
    
    @Query("SELECT r FROM Receipt r WHERE r.customerId = :customerId AND r.receiptDate >= :startDate ORDER BY r.receiptDate DESC")
    List<Receipt> findRecentReceiptsByCustomer(@Param("customerId") String customerId, @Param("startDate") LocalDateTime startDate);
    
    @Query("SELECT r FROM Receipt r WHERE r.orderId = :orderId AND r.status = 'LOST' ORDER BY r.receiptDate DESC")
    List<Receipt> findLostReceiptsByOrder(@Param("orderId") Long orderId);
    
    @Query("SELECT r FROM Receipt r WHERE r.customerId = :customerId AND r.status = 'LOST' ORDER BY r.receiptDate DESC")
    List<Receipt> findLostReceiptsByCustomer(@Param("customerId") String customerId);
    
    boolean existsByReceiptNumber(String receiptNumber);
}
