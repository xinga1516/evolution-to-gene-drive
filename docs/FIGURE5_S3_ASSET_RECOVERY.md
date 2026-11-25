# Figure 5 / Figure S3 runtime-asset recovery

The final replicate outputs are retained locally. Their per-run `status.json`
and `data_metadata.csv` files identify the historical runtime assets exactly:

- SLiM 5.0;
- model `reprising.formal_experiment.pinned.slim`;
- model SHA256 `94e465ec99eaef5646cdfc1828c8121cb0b7df4b4290a0f7622e04624def8812`;
- checkpoint origin seeds 61001--61100;
- checkpoint modes `evolving` and `uniform`;
- branch seed rule `origin_seed + 1000000`.

The earlier transfer script packaged `formal_100_zpg_off/`, which contains the
branch results and logs. The pinned model and checkpoints were outside that
directory, under the parent `final/` tree, so they were not included in the
download. This is a transfer-scope omission, not loss of the final replicate
data or their parameter provenance.

A local historical archive has since been identified at
`D:\缓存\xwechat_files\wxid_n64yngopmpoh12_ff3d\msg\file\2026-10\checkpoints.zip`.
Its SHA256 is
`7684e5c164a8c0fcfe99a4b9d53fc93630e9aa8f12e5cc2e037fefc5390b6811`.
It contains 200 non-empty checkpoints (100 per mode), all seeds 61001--61100,
and the corresponding trait histories and run metadata. The metadata records
the expected pinned-model hash. The pinned model and historical runner are not
inside that archive and still need recovery from the cluster or another backup.

On the cluster, run:

```bash
bash scripts/package_figure5_s3_runtime_assets.sh \
  /lustre2/jchamper_pkuhpc/xinyue/mutation/migration/final \
  "$PWD/figure5_s3_runtime_assets"
```

The script refuses to package a model with the wrong hash or an incomplete
checkpoint tree. A passing package contains the exact model, the historical
runner and 200 complete checkpoint directories, including `data_traits.csv`,
`data_metadata.csv` and `status.json`. The generated `SHA256SUMS.txt` records
the runner hash because no independent historical runner hash is currently
available. Deposit the resulting archive with the
external raw simulation data and record its retrieval URI and archive SHA256
in `data/README.md`. Do not commit the checkpoint binaries to Git.
