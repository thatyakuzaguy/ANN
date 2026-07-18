# ANN Offline Windows Release

The public ANN package is split into GitHub-compatible parts because the
embedded CUDA runtime is larger than the per-asset limit.

1. Download `ANN_RELEASE_PARTS.json`, `ANN_RELEASE_PARTS.sha256`,
   `assemble_release.ps1`, and every `.partNNN` file into one folder on `D:` or
   `E:`.
2. Verify the manifest checksum:

   ```powershell
   Get-FileHash .\ANN_RELEASE_PARTS.json -Algorithm SHA256
   Get-Content .\ANN_RELEASE_PARTS.sha256
   ```

3. Assemble and install:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\assemble_release.ps1 `
     -PartsRoot $PWD `
     -OutputRoot D:\ANN-Release `
     -InstallRoot D:\ANN `
     -RunInstaller
   ```

The assembler verifies every part and the reconstructed archive before
extraction. The installer then verifies every manifest-declared payload file
before copying it.

Model weights are not included. Real local inference remains disabled until an
authorized, hash-verified ANN model pack is installed deliberately.
