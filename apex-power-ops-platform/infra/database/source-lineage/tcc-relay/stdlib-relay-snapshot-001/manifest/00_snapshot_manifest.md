# TCC Relay StdLib Snapshot 001 Manifest

Date: 2026-04-30
Snapshot id: `stdlib-relay-snapshot-001`
Source root: `D:\Access DB\tables\`
Extraction method: byte-for-byte copy of the admitted relay CSV export set into
repo-native shared-infra source-lineage.

Governing packet chain:

1. `Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
4. `Platform-Authority/TCC-RELAY-TRANCHE-2-STAGED-POPULATION-AND-PROVENANCE-REPLAY-EXECUTION-PACKET-2026-04-30.md`

## File Manifest

| File | Bytes | Rows | SHA-256 |
| --- | ---: | ---: | --- |
| Manufacturers.csv | 7133 | 450 | 530e1da85532171b01d1366f02dd3bcc7e8aa1df35f55db40563994a54d99462 |
| Relays.csv | 239512 | 1442 | a97c57f7365220412272ec9cd69f9bf172b8c41813abbf5add8a0ad445dacb61 |
| RelayDevices.csv | 250263 | 7192 | c2793addc8595dfced29f700f5008f25518934f1de7ff5d8f8d3dcae93152d07 |
| RelayLineSection.csv | 764680 | 23991 | e600afd9f15bd643e4bdc8f9a53c4bc9776ae1b6ba6f43280f5a0fd30a8b84e4 |
| RelayTDSection.csv | 208005 | 6956 | 8900289a0d51e96cf1653a79fe38cdbb026ff035ba8e48e19a9db685d181dd47 |
| RelayRanges.csv | 1562071 | 34955 | c872a95a2a9e104f5f6d288c07e7b06e05f90fd8348ae205fc877dac61f16fc1 |
| RelayDiscreteValues.csv | 649889 | 40348 | b540f862c674363fea2b5c606072d0dfbf178bd7c124313648e06265fbb7b860 |
| RelaySec2IEC.csv | 23919 | 995 | ab0593f619899b803873bb1e443cddd0c0cf205a51f9283f848a8bee18e170d0 |
| RelaySec2IECCurves.csv | 170565 | 4164 | ff0007e41e2ffd38a3b2d34d97c086c7b67c571327e081a1b4110ff6d8917286 |
| RelaySec2SWZ.csv | 23051 | 958 | 952d2c452ad9959245d6235e33ed663415091ebdb031a4d542b91f307246dfb1 |
| RelaySec2SWZCurves.csv | 231078 | 5728 | 3848abb9a13fba084c155f2c7642ffb632880a8359b1513d8740ec419b8ce195 |
| RelaySec2BSL.csv | 12061 | 501 | 56b4a450b543eeb881d0a3d66c9d663bfe4ca56de38f0d4ade99130e43044b96 |
| RelaySec2BSLCurves.csv | 209312 | 3715 | 71e80390ed5796897966720da494a41521f6835b2d4e7fb06ae8326b4009b2ef |
| RelaySec2MEQ.csv | 8299 | 344 | 65ba3c7468a01fff1c24ea97c05244de96cf14c1c7664af737af1e1f11328c72 |
| RelaySec2MEQCurves.csv | 86227 | 1644 | 24adc4094272102f567049124a7695a4ed6c65f28102a4c95f3fb6acaa6d33eb |
| RelaySec2PCD.csv | 1313 | 53 | 517d662912393c2d30ba0f3eab434db9f0311345689c434d1c6721f25a48c7c4 |
| RelaySec2PCDCurves.csv | 18757 | 432 | a08ce7ccd5f314cea84e2a5c7e6729b64ba30cb3abcf878ce53857c5c8e3b6ad |
| RelaySec2LRM.csv | 390 | 13 | 6235dda0d855be4b4ccd1142fa280d1afeb9c0f45e823cad1995d419970d3fd2 |
| RelaySec2RXD.csv | 667 | 26 | 45d19e5d8ab968cbbc03cfa7815431a2427e9f7cc2c17cb352754411cc8080e4 |
| RelaySec2EGC.csv | 43 | 0 | ec840857e7769bf82b3ec72b0787cda21efa885e5b86e1f7097daa6befa8242e |
| RelaySec2TCP.csv | 770489 | 18908 | e7658d2349ffc36142d431bcbb89083f74c829ddd653f2b963a29c2cfe528674 |
| RelaySec2TCPCurves.csv | 14868760 | 146912 | 67d2e2744cc50e60593ee83b50130d67f7b5734be18ed37a72433478f91e0b95 |

Snapshot immutability rule:

1. these hashes define `stdlib-relay-snapshot-001`,
2. any corrected export requires a new snapshot id,
3. Tranche 2 replay must not mix files from multiple snapshot ids.