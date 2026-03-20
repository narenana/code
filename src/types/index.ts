export type Category =
  | 'frame'
  | 'flight_controller'
  | 'esc'
  | 'motor'
  | 'vtx'
  | 'camera'
  | 'goggles'
  | 'receiver'
  | 'battery'
  | 'propeller'
  | 'charger'
  | 'gps'
  | 'antenna'
  | 'accessory'
  | 'other'

export interface Manufacturer {
  id: string
  name: string
  slug: string
  website: string | null
  country: string | null
  description: string | null
  logo_url: string | null
}

export interface Product {
  id: string
  name: string
  brand: string
  category: Category
  description: string
  image_url: string
  specs: Record<string, string | number>
  manufacturer_id: string | null
  manufacturer?: Manufacturer
  created_at: string
  updated_at: string
}

export interface Store {
  id: string
  name: string
  url: string
  logo_url: string
}

export interface ProductListing {
  id: string
  product_id: string
  store_id: string
  price_inr: number
  stock: 'in_stock' | 'out_of_stock' | 'unknown'
  product_url: string
  last_checked: string
  store?: Store
}

export interface CompatibilityRule {
  id: string
  category_a: Category
  category_b: Category
  spec_key_a: string
  spec_key_b: string
  operator: 'eq' | 'lte' | 'gte' | 'includes'
  description: string
}

// Spec definitions per category
export const CATEGORY_SPECS: Record<Category, string[]> = {
  frame: ['size_mm', 'motor_mount_mm', 'stack_mount_mm', 'weight_g', 'material', 'prop_size'],
  flight_controller: ['stack_mount_mm', 'gyro', 'processor', 'input_voltage', 'uart_count', 'weight_g'],
  esc: ['stack_mount_mm', 'current_a', 'cell_count', 'protocol', 'weight_g'],
  motor: ['motor_mount_mm', 'stator_size', 'kv', 'cell_count', 'max_current_a', 'weight_g'],
  vtx: ['stack_mount_mm', 'power_mw', 'protocol', 'input_voltage', 'weight_g'],
  camera: ['sensor', 'fov_deg', 'resolution', 'voltage', 'weight_g'],
  goggles: ['display_type', 'resolution', 'fov_deg', 'protocol', 'battery_type'],
  receiver: ['protocol', 'input_voltage', 'weight_g'],
  battery: ['cell_count', 'capacity_mah', 'discharge_c', 'weight_g', 'connector'],
  propeller: ['size_inch', 'pitch', 'blade_count', 'motor_mount_mm', 'material'],
  charger: ['max_power_w', 'cell_count_max', 'connector', 'input_voltage'],
  gps: ['protocol', 'baud_rate', 'weight_g'],
  antenna: ['connector', 'frequency', 'gain_dbi', 'weight_g'],
  accessory: ['weight_g'],
  other: ['weight_g'],
}

export const CATEGORY_LABELS: Record<Category, string> = {
  frame: 'Frame',
  flight_controller: 'Flight Controller',
  esc: 'ESC',
  motor: 'Motor',
  vtx: 'Video Transmitter',
  camera: 'Camera',
  goggles: 'Goggles',
  receiver: 'Receiver',
  battery: 'Battery',
  propeller: 'Propeller',
  charger: 'Charger',
  gps: 'GPS',
  antenna: 'Antenna',
  accessory: 'Accessory',
  other: 'Other',
}

export const COMPATIBILITY_PAIRS: Array<{
  a: Category
  b: Category
  rules: Array<{ specA: string; specB: string; label: string }>
}> = [
  {
    a: 'frame',
    b: 'motor',
    rules: [{ specA: 'motor_mount_mm', specB: 'motor_mount_mm', label: 'Motor mount pattern' }],
  },
  {
    a: 'frame',
    b: 'flight_controller',
    rules: [{ specA: 'stack_mount_mm', specB: 'stack_mount_mm', label: 'Stack mount pattern' }],
  },
  {
    a: 'frame',
    b: 'esc',
    rules: [{ specA: 'stack_mount_mm', specB: 'stack_mount_mm', label: 'Stack mount pattern' }],
  },
  {
    a: 'esc',
    b: 'motor',
    rules: [{ specA: 'cell_count', specB: 'cell_count', label: 'Cell count (voltage)' }],
  },
  {
    a: 'battery',
    b: 'esc',
    rules: [{ specA: 'cell_count', specB: 'cell_count', label: 'Cell count (voltage)' }],
  },
  {
    a: 'battery',
    b: 'motor',
    rules: [{ specA: 'cell_count', specB: 'cell_count', label: 'Cell count (voltage)' }],
  },
]
