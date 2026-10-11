<template>
	<div class="flex flex-col min-h-0 text-base">
		<div class="flex items-center justify-between mb-5">
			<div class="flex items-center space-x-2">
				<Button variant="ghost" @click="emit('close')">
					<ChevronLeft class="h-4 w-4 stroke-1.5" />
				</Button>
				<div class="text-xl font-semibold text-ink-gray-9">
					{{ isNew ? __('New Certificate Template') : template.template_name }}
				</div>
			</div>
			<div class="flex items-center space-x-2">
				<Button :loading="previewingPdf" @click="previewPdf">
					{{ __('Preview PDF') }}
				</Button>
				<Button variant="solid" :loading="saving" @click="save">
					{{ __('Save') }}
				</Button>
			</div>
		</div>

		<div class="overflow-y-auto space-y-5 pr-1">
			<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
				<FormControl
					v-model="template.template_name"
					:label="__('Template Name')"
					:disabled="!isNew"
					:required="true"
				/>
				<FormControl
					v-model="template.template_type"
					type="select"
					:label="__('Template Type')"
					:options="typeOptions"
				/>
				<FormControl
					v-model="template.page_size"
					type="select"
					:label="__('Page Size')"
					:options="['A4', 'Letter']"
				/>
				<FormControl
					v-model="template.orientation"
					type="select"
					:label="__('Orientation')"
					:options="orientationOptions"
				/>
				<div class="flex items-end pb-1">
					<FormControl
						v-model="template.enabled"
						type="checkbox"
						:label="__('Enabled')"
					/>
				</div>
				<div class="flex items-end pb-1">
					<FormControl
						v-model="template.include_grades_page"
						type="checkbox"
						:label="__('Include grades page')"
					/>
				</div>
			</div>

			<template v-if="template.template_type === 'HTML'">
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
					<div class="space-y-3">
						<CodeEditor
							ref="htmlEditor"
							v-model="template.html"
							type="HTML"
							:label="__('HTML')"
							height="260px"
							:autofocus="false"
							:showLineNumbers="true"
							:liveUpdate="true"
							:autoPair="false"
						/>
						<CodeEditor
							v-model="template.css"
							type="CSS"
							:label="__('CSS')"
							height="200px"
							:autofocus="false"
							:showLineNumbers="true"
							:liveUpdate="true"
							:autoPair="false"
						/>
						<div>
							<div class="text-xs text-ink-gray-5 mb-1.5">
								{{ __('Click a placeholder to insert it') }}
							</div>
							<div class="flex flex-wrap gap-1.5">
								<button
									v-for="item in PLACEHOLDERS"
									:key="item.key"
									type="button"
									class="rounded bg-surface-gray-2 px-1.5 py-0.5 text-xs text-ink-gray-7 hover:bg-surface-gray-3"
									:title="__(item.description)"
									@click="insertPlaceholder(item.key)"
								>
									{{ item.key }}
								</button>
							</div>
						</div>
					</div>
					<div>
						<div class="text-xs text-ink-gray-5 mb-1.5">
							{{ __('Live preview (sample data)') }}
						</div>
						<div
							ref="previewBox"
							class="relative w-full overflow-hidden border rounded bg-white"
							:style="{ height: `${previewHeight}px` }"
						>
							<!-- No allow-scripts: nothing can run in here. allow-same-origin only lets the preview load the app's fonts. -->
							<iframe
								sandbox="allow-same-origin"
								:srcdoc="previewHtml"
								class="absolute left-0 top-0 border-0 bg-white"
								:style="iframeStyle"
							/>
						</div>
						<div v-if="previewError" class="mt-2 text-xs text-ink-red-3">
							{{ previewError }}
						</div>
					</div>
				</div>
			</template>

			<template v-else>
				<Uploader
					v-model="template.background_image"
					:label="__('Background Image')"
					:description="
						__('The certificate artwork. Match the page proportions.')
					"
				/>
				<CertificateLayoutEditor
					v-model="layout"
					:background="template.background_image"
					:pageSize="template.page_size"
					:orientation="template.orientation"
				/>
			</template>

			<div class="border-t pt-4">
				<div class="text-lg font-semibold text-ink-gray-9 mb-3">
					{{ __('Signers') }}
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					<div v-for="index in [1, 2]" :key="index" class="space-y-3">
						<FormControl
							v-model="template[`signer_${index}_name`]"
							:label="__('Signer {0} Name').format(index)"
						/>
						<FormControl
							v-model="template[`signer_${index}_title`]"
							:label="__('Signer {0} Title').format(index)"
						/>
						<div>
							<div class="text-xs text-ink-gray-5 mb-2">
								{{ __('Signer {0} Signature').format(index) }}
							</div>
							<Uploader v-model="template[`signer_${index}_signature`]" />
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
<script setup>
import { Button, call, FormControl, toast } from 'frappe-ui'
import {
	computed,
	nextTick,
	onBeforeUnmount,
	onMounted,
	reactive,
	ref,
	watch,
} from 'vue'
import { ChevronLeft } from 'lucide-vue-next'
import { cleanError } from '@/utils'
import { getPageSize, PLACEHOLDERS } from '@/utils/certificate'
import CodeEditor from '@/components/Controls/CodeEditor.vue'
import Uploader from '@/components/Controls/Uploader.vue'
import CertificateLayoutEditor from '@/components/Settings/CertificateLayoutEditor.vue'

const props = defineProps({
	templateName: { type: String, default: 'new' },
})
const emit = defineEmits(['close', 'saved'])

const PREVIEW_METHOD =
	'lms.lms.certificate_renderer.preview_certificate_template'
const MM_TO_PX = 96 / 25.4

const isNew = computed(() => props.templateName === 'new')
const saving = ref(false)
const previewingPdf = ref(false)
const previewHtml = ref('')
const previewError = ref('')
const htmlEditor = ref(null)
const previewBox = ref(null)
const previewWidth = ref(0)
const layout = ref([])

const defaults = () => ({
	template_name: '',
	template_type: 'HTML',
	enabled: 1,
	include_grades_page: 0,
	page_size: 'A4',
	orientation: 'Landscape',
	html: '',
	css: '',
	background_image: '',
	signer_1_name: '',
	signer_1_title: '',
	signer_1_signature: '',
	signer_2_name: '',
	signer_2_title: '',
	signer_2_signature: '',
})
const template = reactive(defaults())

const typeOptions = [
	{ label: __('HTML'), value: 'HTML' },
	{ label: __('Image'), value: 'Image' },
]
const orientationOptions = [
	{ label: __('Landscape'), value: 'Landscape' },
	{ label: __('Portrait'), value: 'Portrait' },
]

const toPayload = () => {
	const payload = {
		...template,
		enabled: template.enabled ? 1 : 0,
		include_grades_page: template.include_grades_page ? 1 : 0,
	}
	payload.layout_json = JSON.stringify(layout.value)
	return payload
}

const load = async () => {
	Object.assign(template, defaults())
	layout.value = []
	if (isNew.value) return
	const doc = await call('frappe.client.get', {
		doctype: 'LMS Certificate Template',
		name: props.templateName,
	})
	Object.keys(defaults()).forEach((key) => {
		template[key] = doc[key] ?? defaults()[key]
	})
	try {
		layout.value = JSON.parse(doc.layout_json || '[]')
	} catch (e) {
		layout.value = []
	}
}

const parseMessages = (text) => {
	try {
		const messages = JSON.parse(text)
		return messages
			.map((message) => {
				try {
					return JSON.parse(message).message
				} catch (e) {
					return message
				}
			})
			.map((message) => cleanError(message))
			.join(' ')
	} catch (e) {
		return ''
	}
}

const insertPlaceholder = (key) => {
	htmlEditor.value?.insertAtCursor(`{{ ${key} }}`)
}

// Live HTML preview
let timer = null
let requestId = 0
const refreshPreview = () => {
	if (template.template_type !== 'HTML') return
	clearTimeout(timer)
	timer = setTimeout(async () => {
		const current = ++requestId
		try {
			const html = await call(PREVIEW_METHOD, {
				template: JSON.stringify(toPayload()),
				format: 'html',
			})
			if (current !== requestId) return
			previewHtml.value = html
			previewError.value = ''
		} catch (err) {
			if (current !== requestId) return
			previewError.value =
				cleanError(err.messages?.[0]) || err.message || __('Preview failed')
		}
	}, 600)
}

watch(
	() => [
		template.html,
		template.css,
		template.page_size,
		template.orientation,
		template.template_type,
		template.signer_1_name,
		template.signer_1_title,
		template.signer_1_signature,
		template.signer_2_name,
		template.signer_2_title,
		template.signer_2_signature,
	],
	refreshPreview,
)

const pageSize = computed(() =>
	getPageSize(template.page_size, template.orientation),
)
const scale = computed(() =>
	previewWidth.value
		? previewWidth.value / (pageSize.value.width * MM_TO_PX)
		: 0.5,
)
const previewHeight = computed(
	() => pageSize.value.height * MM_TO_PX * scale.value,
)
const iframeStyle = computed(() => ({
	width: `${pageSize.value.width}mm`,
	height: `${pageSize.value.height}mm`,
	transform: `scale(${scale.value})`,
	transformOrigin: 'top left',
}))

let observer = null
const measure = () => {
	previewWidth.value = previewBox.value?.clientWidth || 0
}
onMounted(async () => {
	await load()
	await nextTick()
	if (template.template_type === 'HTML') {
		refreshPreview()
	}
	if (typeof ResizeObserver !== 'undefined') {
		observer = new ResizeObserver(measure)
		watch(previewBox, (el) => el && observer.observe(el), { immediate: true })
	}
	measure()
})
onBeforeUnmount(() => {
	clearTimeout(timer)
	observer?.disconnect()
})

const previewPdf = async () => {
	// Open the tab synchronously so the browser does not block the popup.
	const tab = window.open('', '_blank')
	previewingPdf.value = true
	try {
		const body = new URLSearchParams({
			template: JSON.stringify(toPayload()),
			format: 'pdf',
		})
		const response = await fetch(`/api/method/${PREVIEW_METHOD}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded',
				'X-Frappe-CSRF-Token': window.csrf_token,
			},
			body,
		})
		const contentType = response.headers.get('content-type') || ''
		if (response.ok && contentType.includes('pdf')) {
			const blob = await response.blob()
			const url = URL.createObjectURL(blob)
			if (tab) tab.location.href = url
		} else {
			tab?.close()
			let message = ''
			try {
				const data = await response.json()
				message = data._server_messages
					? parseMessages(data._server_messages)
					: ''
				message = message || cleanError(data.exception || '')
			} catch (e) {
				// not JSON
			}
			toast.error(message || __('Could not generate the PDF preview'))
		}
	} catch (e) {
		tab?.close()
		toast.error(__('Could not generate the PDF preview'))
	} finally {
		previewingPdf.value = false
	}
}

const save = async () => {
	if (!template.template_name?.trim()) {
		toast.error(__('Template name is required'))
		return
	}
	saving.value = true
	try {
		const payload = toPayload()
		if (isNew.value) {
			await call('frappe.client.insert', {
				doc: { doctype: 'LMS Certificate Template', ...payload },
			})
		} else {
			const { template_name, ...values } = payload
			await call('frappe.client.set_value', {
				doctype: 'LMS Certificate Template',
				name: props.templateName,
				fieldname: values,
			})
		}
		toast.success(__('Certificate template saved'))
		emit('saved')
		emit('close')
	} catch (err) {
		toast.error(
			cleanError(err.messages?.[0]) ||
				err.message ||
				__('Error saving template'),
		)
	} finally {
		saving.value = false
	}
}
</script>
