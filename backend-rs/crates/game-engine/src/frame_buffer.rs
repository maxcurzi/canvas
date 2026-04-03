use serde::{Deserialize, Serialize};

const TILE_SIZE: u16 = 16;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FrameBuffer {
    width: u16,
    height: u16,
    pixels: Vec<u8>,
    dirty_tiles: Vec<bool>,
    tiles_x: u16,
    tiles_y: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TileDelta {
    pub tile_x: u16,
    pub tile_y: u16,
    pub data: Vec<u8>,
}

impl FrameBuffer {
    pub fn new(width: u16, height: u16) -> Self {
        let tiles_x = (width + TILE_SIZE - 1) / TILE_SIZE;
        let tiles_y = (height + TILE_SIZE - 1) / TILE_SIZE;
        Self {
            width,
            height,
            pixels: vec![0; width as usize * height as usize],
            dirty_tiles: vec![true; tiles_x as usize * tiles_y as usize],
            tiles_x,
            tiles_y,
        }
    }

    pub fn width(&self) -> u16 {
        self.width
    }

    pub fn height(&self) -> u16 {
        self.height
    }

    pub fn pixels(&self) -> &[u8] {
        &self.pixels
    }

    pub fn get_pixel(&self, x: u16, y: u16) -> u8 {
        if x >= self.width || y >= self.height {
            return 0;
        }
        self.pixels[y as usize * self.width as usize + x as usize]
    }

    pub fn set_pixel(&mut self, x: u16, y: u16, color_index: u8) {
        if x >= self.width || y >= self.height {
            return;
        }
        let idx = y as usize * self.width as usize + x as usize;
        if self.pixels[idx] != color_index {
            self.pixels[idx] = color_index;
            let tile_x = x / TILE_SIZE;
            let tile_y = y / TILE_SIZE;
            self.dirty_tiles[tile_y as usize * self.tiles_x as usize + tile_x as usize] = true;
        }
    }

    pub fn fill(&mut self, color_index: u8) {
        self.pixels.fill(color_index);
        self.dirty_tiles.fill(true);
    }

    pub fn extract_dirty_tiles(&mut self) -> Vec<TileDelta> {
        let mut deltas = Vec::new();
        for ty in 0..self.tiles_y {
            for tx in 0..self.tiles_x {
                let tile_idx = ty as usize * self.tiles_x as usize + tx as usize;
                if !self.dirty_tiles[tile_idx] {
                    continue;
                }
                self.dirty_tiles[tile_idx] = false;
                let start_x = tx * TILE_SIZE;
                let start_y = ty * TILE_SIZE;
                let end_x = (start_x + TILE_SIZE).min(self.width);
                let end_y = (start_y + TILE_SIZE).min(self.height);
                let tile_w = (end_x - start_x) as usize;
                let tile_h = (end_y - start_y) as usize;
                let mut data = Vec::with_capacity(tile_w * tile_h);
                for row in start_y..end_y {
                    let row_start = row as usize * self.width as usize + start_x as usize;
                    data.extend_from_slice(&self.pixels[row_start..row_start + tile_w]);
                }
                deltas.push(TileDelta {
                    tile_x: tx,
                    tile_y: ty,
                    data,
                });
            }
        }
        deltas
    }

    pub fn has_dirty_tiles(&self) -> bool {
        self.dirty_tiles.iter().any(|&d| d)
    }

    pub fn mark_all_clean(&mut self) {
        self.dirty_tiles.fill(false);
    }

    pub fn mark_all_dirty(&mut self) {
        self.dirty_tiles.fill(true);
    }

    pub fn downsample(&self, target_width: u16, target_height: u16) -> Vec<u8> {
        let mut result = vec![0u8; target_width as usize * target_height as usize];
        let scale_x = self.width as f32 / target_width as f32;
        let scale_y = self.height as f32 / target_height as f32;
        for ty in 0..target_height {
            for tx in 0..target_width {
                let src_x = (tx as f32 * scale_x) as u16;
                let src_y = (ty as f32 * scale_y) as u16;
                result[ty as usize * target_width as usize + tx as usize] =
                    self.get_pixel(src_x.min(self.width - 1), src_y.min(self.height - 1));
            }
        }
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_buffer_is_zeroed() {
        let fb = FrameBuffer::new(32, 32);
        assert_eq!(fb.width(), 32);
        assert_eq!(fb.height(), 32);
        assert!(fb.pixels().iter().all(|&p| p == 0));
    }

    #[test]
    fn set_and_get_pixel() {
        let mut fb = FrameBuffer::new(64, 64);
        fb.set_pixel(10, 20, 5);
        assert_eq!(fb.get_pixel(10, 20), 5);
        assert_eq!(fb.get_pixel(0, 0), 0);
    }

    #[test]
    fn out_of_bounds_returns_zero() {
        let fb = FrameBuffer::new(32, 32);
        assert_eq!(fb.get_pixel(100, 100), 0);
    }

    #[test]
    fn set_pixel_out_of_bounds_is_noop() {
        let mut fb = FrameBuffer::new(32, 32);
        fb.set_pixel(100, 100, 5);
        // Should not panic, no effect
    }

    #[test]
    fn dirty_tiles_track_changes() {
        let mut fb = FrameBuffer::new(64, 64);
        fb.mark_all_clean();
        assert!(!fb.has_dirty_tiles());

        fb.set_pixel(10, 10, 1);
        assert!(fb.has_dirty_tiles());
    }

    #[test]
    fn extract_dirty_tiles_returns_changed_tiles() {
        let mut fb = FrameBuffer::new(64, 64);
        fb.mark_all_clean();

        fb.set_pixel(0, 0, 1);
        fb.set_pixel(32, 32, 2);

        let deltas = fb.extract_dirty_tiles();
        assert_eq!(deltas.len(), 2);
        assert_eq!(deltas[0].tile_x, 0);
        assert_eq!(deltas[0].tile_y, 0);
        assert_eq!(deltas[1].tile_x, 2);
        assert_eq!(deltas[1].tile_y, 2);
    }

    #[test]
    fn extract_clears_dirty_flags() {
        let mut fb = FrameBuffer::new(32, 32);
        fb.mark_all_clean();
        fb.set_pixel(5, 5, 1);
        let _ = fb.extract_dirty_tiles();
        assert!(!fb.has_dirty_tiles());
    }

    #[test]
    fn fill_sets_all_pixels_and_marks_dirty() {
        let mut fb = FrameBuffer::new(16, 16);
        fb.mark_all_clean();
        fb.fill(7);
        assert!(fb.pixels().iter().all(|&p| p == 7));
        assert!(fb.has_dirty_tiles());
    }

    #[test]
    fn same_value_set_does_not_dirty() {
        let mut fb = FrameBuffer::new(32, 32);
        fb.mark_all_clean();
        fb.set_pixel(5, 5, 0); // already 0
        assert!(!fb.has_dirty_tiles());
    }

    #[test]
    fn tile_data_contains_correct_pixels() {
        let mut fb = FrameBuffer::new(32, 32);
        fb.mark_all_clean();
        fb.set_pixel(0, 0, 42);
        let deltas = fb.extract_dirty_tiles();
        assert_eq!(deltas.len(), 1);
        assert_eq!(deltas[0].data[0], 42);
        assert_eq!(deltas[0].data.len(), 16 * 16);
    }

    #[test]
    fn non_tile_aligned_canvas() {
        let fb = FrameBuffer::new(20, 20);
        assert_eq!(fb.width(), 20);
        assert_eq!(fb.height(), 20);
        // 20/16 = 1.25 -> 2 tiles per axis
        // Initial state: all dirty
        assert!(fb.has_dirty_tiles());
    }

    #[test]
    fn edge_tile_has_correct_size() {
        let mut fb = FrameBuffer::new(20, 20);
        fb.mark_all_clean();
        fb.set_pixel(18, 18, 1); // In edge tile (1,1)
        let deltas = fb.extract_dirty_tiles();
        assert_eq!(deltas.len(), 1);
        assert_eq!(deltas[0].tile_x, 1);
        assert_eq!(deltas[0].tile_y, 1);
        // Edge tile is 4x4 (20 - 16 = 4)
        assert_eq!(deltas[0].data.len(), 4 * 4);
    }

    #[test]
    fn downsample_produces_correct_size() {
        let fb = FrameBuffer::new(64, 64);
        let thumb = fb.downsample(16, 16);
        assert_eq!(thumb.len(), 16 * 16);
    }

    #[test]
    fn downsample_preserves_pixel_values() {
        let mut fb = FrameBuffer::new(32, 32);
        fb.fill(5);
        let thumb = fb.downsample(8, 8);
        assert!(thumb.iter().all(|&p| p == 5));
    }
}
