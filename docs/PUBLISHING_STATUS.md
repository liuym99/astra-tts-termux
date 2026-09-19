# Publishing status

## Completed

- Public repository structure and documentation
- MIT license and security guidance
- Portable service and conversion scripts
- `chenxing` model Git LFS pointer files
- `chenxing` model SHA-256 manifest
- Two licensed `chenxing` WAV reference-audio files
- WAV header validation and combined model/audio manifest
- Python and Bash syntax checks
- Sensitive path and generated-file scan
- Source archive: `/sdcard/astra-tts-github-source.zip`

## Pending before pushing to GitHub

1. Add the exact upstream model and reference-audio attribution and full license text.
2. Install Git and Git LFS in the publishing environment.
3. Run `git lfs install`, initialize the repository, commit, and push.
4. Verify a clean clone with `git lfs pull`, manifest checks, and the documented service checks.

The five ONNX files are Git LFS pointers. The two WAV reference files are included directly because they are small.
