# worker-mochi

> Generate videos with Mochi as an endpoint on RunPod

## Features

- Video generation using [Mochi 1](https://github.com/genmoai/mochi) by [Genmo](https://genmo.ai)
- Automatic model loading and initialization
- [UploadThing](https://uploadthing.com/) integration for video upload

## API Reference

### Input Parameters

```json
{
  "input": {
    "positive_prompt": "a cat playing with yarn, cute, fluffy, detailed fur",
    "negative_prompt": "",
    "width": 848,
    "height": 480,
    "seed": 42,
    "steps": 40,
    "cfg": 6,
    "num_frames": 31,
    "vae": {
      "enable_vae_tiling": false,
      "tile_sample_min_width": 312,
      "tile_sample_min_height": 160,
      "tile_overlap_factor_width": 0.25,
      "tile_overlap_factor_height": 0.25,
      "auto_tile_size": false,
      "frame_batch_size": 8
    }
  }
}
```

#### Core Parameters

| Parameter         | Description                                                            | Default |
| ----------------- | ---------------------------------------------------------------------- | ------- |
| `positive_prompt` | Text description of what you want to generate                          | `""`    |
| `negative_prompt` | Text description of what you want to avoid in the generation           | `""`    |
| `width`           | Output video width in pixels                                           | `848`   |
| `height`          | Output video height in pixels                                          | `480`   |
| `seed`            | Random seed for reproducible results                                   | `1337`  |
| `steps`           | Number of denoising steps (higher = better quality, slower generation) | `40`    |
| `cfg`             | Classifier-free guidance scale (how closely to follow the prompt)      | `6`     |
| `num_frames`      | Number of frames to generate                                           | `31`    |

#### VAE Parameters

| Parameter                    | Description                                | Default |
| ---------------------------- | ------------------------------------------ | ------- |
| `enable_vae_tiling`          | Enable tiling for VAE decoding             | `false` |
| `tile_sample_min_width`      | Minimum tile width when tiling is enabled  | `312`   |
| `tile_sample_min_height`     | Minimum tile height when tiling is enabled | `160`   |
| `tile_overlap_factor_width`  | Overlap factor between tiles (width)       | `0.25`  |
| `tile_overlap_factor_height` | Overlap factor between tiles (height)      | `0.25`  |
| `auto_tile_size`             | Automatically determine tile size          | `false` |
| `frame_batch_size`           | Number of frames to process in parallel    | `8`     |

## Deployment

Deploy this worker on RunPod using the [GitHub Integration](https://docs.runpod.io/serverless/github-integration).

## Development

For development and contribution guidelines, please see our [Contributing Guide](.github/CONTRIBUTING.md).

## License

[MIT License](LICENSE)
