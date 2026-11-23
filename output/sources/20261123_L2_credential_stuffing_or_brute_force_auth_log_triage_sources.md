# Sources for Credential Stuffing or Brute Force? Auth Log Triage

    ## Inspired by
    Loosely inspired by the BOLA and API abuse cases in https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization and the first-symptom misclassification problem common in SOC practice. Arcade staff see login timeouts and call every incident a DDoS, while the logs show a credential stuffing wave.

    ## Concepts tested
    - Indicators of compromise: bursts of failed authentications
- Distinguishing attack categories by vector, target and impact
- Detection false positives from shared NAT addresses

    ## Trap
    The statement says the burst threshold is 20 accounts, but a burst of exactly 20 distinct accounts must count as credential stuffing (at least, not greater than). Naive solutions use > and misclassify the boundary case as unknown. The statement mentions shared NAT but does not say which rule wins when a NAT IP also shows many failures; the listed order resolves it.

    ## Key concepts found for the topic
    - Attack surface mapping: identifying exposed services, APIs, and device interfaces before classifying attack types
- Distinguishing attack categories (phishing, credential stuffing, injection, DoS, man-in-the-middle, supply chain) by vector, target, and impact
- Indicators of compromise: anomalous login geography, bursts of failed authentications, unexpected outbound traffic, and config drift
- Kill chain / MITRE ATT&CK mapping to place observed activity into a sequence of attacker techniques
- Threat actor motivation and capability tiers (opportunistic, criminal, insider, nation-state) shaping likely attack types
- Severity and blast-radius assessment: data exposure vs. service disruption vs. integrity tampering
- Detection false positives: legitimate bursts (launch events, load tests, shared NAT IPs) mistaken for attacks
- Mitigation layering: input validation, rate limiting, MFA, network segmentation, and patch cadence matched to attack type

    ## Searches
    - virtual reality headset company credential stuffing attack postmortem account takeover
- VR multiplayer game server DDoS incident reflection amplification UDP postmortem
- metaverse platform API broken object level authorization attack case study

    ## Pages found
    - [What is Broken Object Level Authorization? | Indusface Blog](https://www.indusface.com/learning/owasp-api-top-10-broken-object-level-authorization)
- [What Is Broken Object Level Authorization? - Palo Alto Networks](https://www.paloaltonetworks.com/cyberpedia/broken-object-level-authentication-api1)
- [API1:2023 Broken Object Level Authorization - OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization)
- [Defending Against UDP Flood Attacks with Azure DDoS Protection | Microsoft Community Hub](https://techcommunity.microsoft.com/blog/azurenetworksecurityblog/defending-against-udp-flood-attacks-with-azure-ddos-protection/3941758)
- [Amplification Attack Defense: DDoS Protection Guide | A10](https://www.a10networks.com/blog/how-defend-against-amplified-reflection-ddos-attacks)
    