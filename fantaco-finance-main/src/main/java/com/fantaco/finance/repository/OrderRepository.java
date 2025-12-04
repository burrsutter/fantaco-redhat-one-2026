package com.fantaco.finance.repository;

import com.fantaco.finance.entity.Order;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    
    List<Order> findByCustomerIdOrderByOrderDateDesc(String customerId);
    
    List<Order> findByCustomerIdAndOrderDateBetweenOrderByOrderDateDesc(
            String customerId, LocalDateTime startDate, LocalDateTime endDate);
    
    List<Order> findByStatusOrderByOrderDateDesc(Order.OrderStatus status);
    
    @Query("SELECT o FROM Order o WHERE o.customerId = :customerId AND o.orderDate >= :startDate ORDER BY o.orderDate DESC")
    List<Order> findRecentOrdersByCustomer(@Param("customerId") String customerId, @Param("startDate") LocalDateTime startDate);
    
    boolean existsByOrderNumber(String orderNumber);
}
