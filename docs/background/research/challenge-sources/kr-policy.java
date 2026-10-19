package mover.bokji_mate.Service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import mover.bokji_mate.domain.Member;
import mover.bokji_mate.domain.Policy;
import mover.bokji_mate.domain.Scrap;
import mover.bokji_mate.dto.PolicyDto;
import mover.bokji_mate.jwt.JwtTokenProvider;
import mover.bokji_mate.repository.MemberRepository;
import mover.bokji_mate.repository.PolicyRepository;
import mover.bokji_mate.repository.ScrapRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class PolicyService {
    private final PolicyRepository policyRepository;
    private final ScrapRepository scrapRepository;
    private final JwtTokenProvider jwtTokenProvider;
    private final MemberRepository memberRepository;
    private final RedisService redisService;

    //정책 스크랩
    @Transactional
    public void scrapPolicy(String accessToken, Long id) {
        Claims claims = jwtTokenProvider.parseClaims(accessToken);
        String username = claims.getSubject();
        Member findMember = memberRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("Member is not found"));
        Policy findPolicy = policyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Policy is not found"));

        // 중복 스크랩 확인
        if (scrapRepository.existsByMemberAndPolicy(findMember, findPolicy)) {
            throw new RuntimeException("Policy already scrapped by this user.");
        }

        // 스크랩 추가
        Scrap scrap = Scrap.builder()
                .member(findMember)
                .policy(findPolicy)
                .build();
        scrapRepository.save(scrap);
        findMember.setScrapCount(findMember.getScrapCount() + 1);
        findPolicy.setScrapCount(findPolicy.getScrapCount() + 1);
    }

    //스크랩 삭제
    @Transactional
    public void deleteScrap(String accessToken, Long id) {
        Claims claims = jwtTokenProvider.parseClaims(accessToken);
        String username = claims.getSubject();
        Member findMember = memberRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("Member is not found"));
        Policy findPolicy = policyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Policy is not found"));
        Scrap findScrap = scrapRepository.findByMemberAndPolicy(findMember, findPolicy)
                .orElseThrow(() -> new RuntimeException("Scrap is not found"));

        scrapRepository.delete(findScrap);
        findMember.setScrapCount(findMember.getScrapCount() - 1);
        findPolicy.setScrapCount(findPolicy.getScrapCount() - 1);
    }

    // 모든 정책 리턴
    @Transactional
    public List<PolicyDto> getAllPolicies() {
        return policyRepository.findAll().stream()
                .map(PolicyDto::toDto)
                .collect(Collectors.toList());
    }

    // 스크랩한 정책 전송
    @Transactional
    public List<PolicyDto> getScraps(String accessToken) {
        Claims claims = jwtTokenProvider.parseClaims(accessToken);
        String username = claims.getSubject();

        List<Scrap> scraps = scrapRepository.findByMemberUsername(username);
        return scraps.stream()
                .map(scrap -> PolicyDto.toDto(scrap.getPolicy()))
                .collect(Collectors.toList());
    }

    //상세 정책 조회
    @Transactional
    public PolicyDto viewPolicy(Long id) {
        Policy findPolicy = policyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Policy is not found"));
        findPolicy.setViews(findPolicy.getViews() + 1);
        PolicyDto policyDto = PolicyDto.toDto(findPolicy);

        return policyDto;
    }

    // 추천 정책 전송
    @Transactional
    public List<PolicyDto> getRecommendation(String accessToken) {
        Claims claims = jwtTokenProvider.parseClaims(accessToken);
        String username = claims.getSubject();

        Member findMember = memberRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("Member is not found"));
        List<String> interests = findMember.getInterests();
        List<Policy> allPolicies = policyRepository.findByCategoriesIn(interests);

        // 추천 정책이 10개 이하일 경우 무작위 정책 추가
        if (allPolicies.size() < 10) {
            List<Policy> randomPolicies = policyRepository.findRandomPolicies(10 - allPolicies.size());
            allPolicies.addAll(randomPolicies);
        }

        // 중복 제거
        return allPolicies.stream()
                .distinct()
                .map(PolicyDto::toDto)
                .collect(Collectors.toList());
    }

    // 정책 검색 기능
    @Transactional(readOnly = true)
    public List<PolicyDto> searchPolicy(String keyword) {
        List<Policy> policies = policyRepository.findByKeyword(keyword);
        //List<Policy> policies = policyRepository.searchByKeyword(keyword);
        return policies.stream()
                .map(PolicyDto::toDto)
                .collect(Collectors.toList());
    }

    @Transactional
    public Boolean isScrapped(String accessToken, Long id) {
        //accesstoken이 없으면 return false, 있는데 정책 스크랩 안했으면 false, 있고 정책스크랩했으면 true
        try {
            Claims claims = jwtTokenProvider.parseClaims(accessToken);
            String username = claims.getSubject();

            if(redisService.getValues(accessToken).equals("false")) {    //false -> 로그인중
                return scrapRepository.existsByMemberUsernameAndPolicyId(username, id);
            }
            return false;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }
}

