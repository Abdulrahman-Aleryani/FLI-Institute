<template>
	<div class="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-4">
		<div>
			<div class="flex items-center justify-between mb-2">
				<div class="text-xs text-ink-gray-5">
					{{ __('Drag a field to move it. Drag its right edge to resize.') }}
				</div>
				<Dropdown :options="addOptions" placement="right">
					<Button>
						<template #prefix>
							<Plus class="h-3 w-3 stroke-1.5" />
						</template>
						{{ __('Add field') }}
					</Button>
				</Dropdown>
			</div>
			<div
				ref="pageEl"
				class="relative w-full overflow-hidden border rounded bg-white select-none"
				:style="{ aspectRatio: `${page.width} / ${page.height}` }"
				tabindex="0"
				@keydown="onKeydown"
				@pointerdown.self="selected = null"
			>
				<img
					v-if="background"
					:src="background"
					class="absolute inset-0 w-full h-full pointer-events-none"
				/>
				<div
					v-for="(element, index) in layout"
					:key="index"
					class="absolute cursor-move border border-dashed"
					:class="
						index === selected
							? 'border-blue-500 bg-blue-500/10'
							: 'border-gray-400'
					"
					:style="boxStyle(element)"
					@pointerdown.stop="startDrag($event, index, 'move')"
				>
					<img
						v-if="isImageField(element.field)"
						:src="placeholderImage(element.field)"
						class="w-full h-auto pointer-events-none"
					/>
					<div v-else :style="textStyle(element)">
						{{ sampleText(element.field) }}
					</div>
					<div
						v-if="isImageField(element.field)"
						class="absolute left-0 top-0 bg-blue-500 text-white text-[10px] px-1"
					>
						{{ fieldLabel(element.field) }}
					</div>
					<div
						class="absolute top-0 right-0 h-full w-2 cursor-ew-resize bg-blue-500/40"
						@pointerdown.stop="startDrag($event, index, 'resize')"
					/>
				</div>
			</div>
		</div>
		<div class="space-y-3">
			<template v-if="current">
				<div class="text-sm font-medium text-ink-gray-9">
					{{ fieldLabel(current.field) }}
				</div>
				<template v-if="!isImageField(current.field)">
					<FormControl
						type="select"
						:label="__('Font')"
						:options="fontOptions"
						:modelValue="current.font_family || DEFAULT_FONT"
						@update:modelValue="(value) => update('font_family', value)"
					/>
					<FormControl
						type="number"
						:label="__('Font size (% of page height)')"
						:modelValue="current.font_size"
						@update:modelValue="(value) => updateNumber('font_size', value)"
					/>
					<div>
						<div class="text-xs text-ink-gray-5 mb-1.5">{{ __('Color') }}</div>
						<input
							type="color"
							class="h-8 w-full rounded border cursor-pointer"
							:value="current.color || '#000000'"
							@input="(event) => update('color', event.target.value)"
						/>
					</div>
					<FormControl
						type="select"
						:label="__('Align')"
						:options="alignOptions"
						:modelValue="current.align || 'left'"
						@update:modelValue="(value) => update('align', value)"
					/>
					<FormControl
						type="checkbox"
						:label="__('Bold')"
						:modelValue="Boolean(current.bold)"
						@update:modelValue="(value) => update('bold', value)"
					/>
					<FormControl
						type="checkbox"
						:label="__('Italic')"
						:modelValue="Boolean(current.italic)"
						@update:modelValue="(value) => update('italic', value)"
					/>
				</template>
				<FormControl
					type="number"
					:label="__('Width (%)')"
					:modelValue="current.width"
					@update:modelValue="(value) => updateNumber('width', value)"
				/>
				<Button variant="subtle" theme="red" class="w-full" @click="remove">
					<template #prefix>
						<Trash2 class="h-3 w-3 stroke-1.5" />
					</template>
					{{ __('Delete') }}
				</Button>
			</template>
			<div v-else class="text-sm text-ink-gray-5">
				{{ __('Select a field to edit it.') }}
			</div>
		</div>
	</div>
</template>
<script setup>
import { Button, Dropdown, FormControl } from 'frappe-ui'
import { computed, ref } from 'vue'
import { Plus, Trash2 } from 'lucide-vue-next'
import {
	clamp,
	DEFAULT_ELEMENT,
	DEFAULT_FONT,
	FONT_FAMILIES,
	getPageSize,
	IMAGE_FIELD_KEYS,
	LAYOUT_FIELDS,
	MAX_LAYOUT_ELEMENTS,
	RANGES,
	SAMPLE_VALUES,
} from '@/utils/certificate'

const layout = defineModel({ type: Array, default: () => [] })
const props = defineProps({
	background: { type: String, default: '' },
	pageSize: { type: String, default: 'A4' },
	orientation: { type: String, default: 'Landscape' },
})

const pageEl = ref(null)
const selected = ref(null)
const page = computed(() => getPageSize(props.pageSize, props.orientation))
const current = computed(() => layout.value[selected.value] || null)

const fontOptions = Object.keys(FONT_FAMILIES).map((name) => ({
	label: name,
	value: name,
}))
const alignOptions = [
	{ label: __('Left'), value: 'left' },
	{ label: __('Center'), value: 'center' },
	{ label: __('Right'), value: 'right' },
]

const isImageField = (field) => IMAGE_FIELD_KEYS.includes(field)
const fieldLabel = (field) =>
	__(LAYOUT_FIELDS.find((item) => item.key === field)?.label || field)
const sampleText = (field) => SAMPLE_VALUES[field] || ''
const placeholderImage = (field) => {
	const label = encodeURIComponent(fieldLabel(field))
	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"><rect width="200" height="100" fill="#e5e7eb"/><text x="100" y="55" font-size="14" text-anchor="middle" fill="#6b7280">${decodeURIComponent(label)}</text></svg>`
	return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

const addOptions = computed(() =>
	LAYOUT_FIELDS.map((field) => ({
		label: __(field.label),
		onClick: () => addField(field.key),
	})),
)

const pageHeightPx = () => pageEl.value?.getBoundingClientRect().height || 0

const boxStyle = (element) => ({
	left: `${element.x}%`,
	top: `${element.y}%`,
	width: `${element.width}%`,
})

// The renderer shrinks long student names proportionally.
const LONG_NAME_LENGTH = 28

const fontScale = (element) => {
	const length = sampleText(element.field).length
	return element.field == 'student_name' && length > LONG_NAME_LENGTH
		? LONG_NAME_LENGTH / length
		: 1
}

const textStyle = (element) => ({
	fontFamily: FONT_FAMILIES[element.font_family || DEFAULT_FONT],
	fontSize: `${((element.font_size || 3) * pageHeightPx() * fontScale(element)) / 100}px`,
	lineHeight: 1.15,
	color: element.color || '#000000',
	textAlign: element.align || 'left',
	fontWeight: element.bold ? 'bold' : 'normal',
	fontStyle: element.italic ? 'italic' : 'normal',
	whiteSpace: 'nowrap',
	overflow: 'hidden',
})

const addField = (field) => {
	if (layout.value.length >= MAX_LAYOUT_ELEMENTS) return
	const element = { field, ...DEFAULT_ELEMENT }
	if (isImageField(field)) {
		delete element.font_size
		delete element.color
		element.width = 15
	}
	layout.value = [...layout.value, element]
	selected.value = layout.value.length - 1
}

const patch = (index, changes) => {
	layout.value = layout.value.map((element, i) =>
		i === index ? { ...element, ...changes } : element,
	)
}

const update = (key, value) => patch(selected.value, { [key]: value })
const updateNumber = (key, value) =>
	patch(selected.value, { [key]: clamp(Number(value), RANGES[key]) })

const remove = () => {
	layout.value = layout.value.filter((_, i) => i !== selected.value)
	selected.value = null
}

let drag = null
const startDrag = (event, index, mode) => {
	selected.value = index
	const rect = pageEl.value.getBoundingClientRect()
	drag = {
		index,
		mode,
		rect,
		startX: event.clientX,
		startY: event.clientY,
		origin: { ...layout.value[index] },
	}
	event.currentTarget.setPointerCapture(event.pointerId)
	event.currentTarget.onpointermove = onDrag
	event.currentTarget.onpointerup = endDrag
	event.currentTarget.onpointercancel = endDrag
	pageEl.value.focus()
}

const onDrag = (event) => {
	if (!drag) return
	const dx = ((event.clientX - drag.startX) / drag.rect.width) * 100
	const dy = ((event.clientY - drag.startY) / drag.rect.height) * 100
	if (drag.mode === 'move') {
		patch(drag.index, {
			x: clamp(round(drag.origin.x + dx), RANGES.x),
			y: clamp(round(drag.origin.y + dy), RANGES.y),
		})
	} else {
		patch(drag.index, {
			width: clamp(round(drag.origin.width + dx), RANGES.width),
		})
	}
}

const endDrag = (event) => {
	if (event.currentTarget) {
		event.currentTarget.onpointermove = null
		event.currentTarget.onpointerup = null
		event.currentTarget.onpointercancel = null
	}
	drag = null
}

const round = (value) => Math.round(value * 100) / 100

const onKeydown = (event) => {
	if (selected.value === null || !current.value) return
	if (event.key === 'Delete') {
		event.preventDefault()
		remove()
		return
	}
	const step = event.shiftKey ? 5 : 0.5
	const moves = {
		ArrowLeft: ['x', -step],
		ArrowRight: ['x', step],
		ArrowUp: ['y', -step],
		ArrowDown: ['y', step],
	}
	const move = moves[event.key]
	if (!move) return
	event.preventDefault()
	const [key, delta] = move
	update(key, clamp(round(current.value[key] + delta), RANGES[key]))
}
</script>
