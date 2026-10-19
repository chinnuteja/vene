package mover.bokji_mate.repository;

import mover.bokji_mate.domain.Policy;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.util.List;

public interface PolicyRepository extends JpaRepository<Policy, Long> {
/*
    @Query("SELECT DISTINCT p FROM Policy p " +
            "WHERE LOWER(p.title) LIKE LOWER(CONCAT('%', :keyword, '%')) " +
            "OR LOWER(p.content) LIKE LOWER(CONCAT('%', :keyword, '%'))")
    List<Policy> searchByKeyword(@Param("keyword") String keyword);

 */

    @Query("SELECT DISTINCT p FROM Policy p WHERE p.title LIKE %:keyword% OR p.content LIKE %:keyword%")
    List<Policy> findByKeyword(@Param("keyword") String keyword);
    List<Policy> findByEndDate(LocalDate endDate);
    List<Policy> findByCategoriesIn(List<String> categories);

    @Query("SELECT p FROM Policy p ORDER BY RAND() LIMIT :limit")
    List<Policy> findRandomPolicies(@Param("limit") int limit);
}

