# Hardware Matrix Candidate Report

Status: `PENDING_EXTERNAL_MACHINE`

ANN has one locally validated Windows 11 workstation. The release policy requires
two independent machines with two distinct GPU profiles, so this report cannot
approve the production hardware gate.

## Primary workstation

- Machine ID: `primary-validation-workstation`
- OS: Windows 11 Pro
- GPU: NVIDIA GeForce RTX 3060 Ti, 8 GB VRAM
- CPU: AMD Ryzen 5 2600
- Memory: 32 GB DDR4
- Isolated install verification: `PASSED`
- Desktop API and web startup smoke: `PASSED`
- Full uninstall with zero residual install directory: `PASSED`
- Real sequential model campaign: `PASSED`
- Autonomous project campaign: `PASSED`
- Clean operating-system image: not established

## Missing evidence

1. A second Windows 11 machine.
2. A second distinct GPU profile.
3. Clean-image installer, inference, project, and uninstaller evidence on both
   machines under the same release snapshot.

No second machine or GPU result is inferred from containers, virtual environments,
or repeated runs on the primary workstation.
