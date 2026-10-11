<template>
	<CertificateTemplateForm
		v-if="showForm"
		:templateName="selectedTemplate"
		@close="closeForm"
		@saved="onSaved"
	/>
	<div v-else class="flex flex-col min-h-0 text-base">
		<div class="flex items-center justify-between mb-5">
			<div class="flex flex-col space-y-2">
				<div class="text-xl font-semibold text-ink-gray-9">
					{{ __(label) }}
				</div>
				<div class="text-ink-gray-6 leading-5">
					{{ __(description) }}
				</div>
			</div>
			<Button @click="openForm('new')">
				<template #prefix>
					<Plus class="h-3 w-3 stroke-1.5" />
				</template>
				{{ __('New') }}
			</Button>
		</div>
		<div v-if="templates.data?.length" class="overflow-y-scroll">
			<ListView
				:columns="columns"
				:rows="templates.data"
				row-key="name"
				:options="{
					showTooltip: false,
					selectable: false,
				}"
			>
				<ListHeader
					class="mb-2 grid items-center space-x-4 rounded bg-surface-gray-2 p-2"
				>
					<ListHeaderItem
						:item="item"
						v-for="item in columns"
						:key="item.key"
					/>
				</ListHeader>
				<ListRows>
					<ListRow :row="row" v-for="row in templates.data" :key="row.name">
						<template #default="{ column }">
							<ListRowItem :item="row[column.key]" :align="column.align">
								<div
									v-if="column.key == 'template_name'"
									class="flex items-center space-x-2 leading-5 text-sm"
								>
									<span
										class="cursor-pointer hover:underline"
										@click="openForm(row.name)"
									>
										{{ row.template_name }}
									</span>
									<Badge v-if="row.name == defaultTemplate" theme="blue">
										{{ __('Default') }}
									</Badge>
								</div>
								<div v-else-if="column.key == 'template_type'" class="text-sm">
									{{ __(row.template_type) }}
								</div>
								<div v-else-if="column.key == 'page'" class="text-sm">
									{{ row.page_size }} · {{ __(row.orientation) }}
								</div>
								<FormControl
									v-else-if="column.key == 'enabled'"
									type="checkbox"
									:modelValue="Boolean(row.enabled)"
									@update:modelValue="(value) => toggleEnabled(row, value)"
								/>
								<Dropdown
									v-else
									:options="getMoreOptions(row)"
									:button="{ icon: 'more-horizontal' }"
									placement="right"
								/>
							</ListRowItem>
						</template>
					</ListRow>
				</ListRows>
			</ListView>
		</div>
		<div v-else class="text-sm italic text-ink-gray-5">
			{{ __('No certificate templates yet.') }}
		</div>
	</div>
</template>
<script setup>
import {
	Badge,
	Button,
	call,
	createListResource,
	createResource,
	Dropdown,
	FormControl,
	ListView,
	ListHeader,
	ListHeaderItem,
	ListRows,
	ListRow,
	ListRowItem,
	toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import { Plus } from 'lucide-vue-next'
import { cleanError } from '@/utils'
import CertificateTemplateForm from '@/components/Settings/CertificateTemplateForm.vue'

const props = defineProps({
	label: {
		type: String,
		default: 'Certificate Templates',
	},
	description: {
		type: String,
		default: '',
	},
})

const showForm = ref(false)
const selectedTemplate = ref('new')

const templates = createListResource({
	doctype: 'LMS Certificate Template',
	fields: [
		'name',
		'template_name',
		'template_type',
		'page_size',
		'orientation',
		'enabled',
	],
	orderBy: 'modified desc',
	pageLength: 100,
	auto: true,
})

const settings = createResource({
	url: 'frappe.client.get_value',
	params: {
		doctype: 'LMS Settings',
		fieldname: 'default_certificate_template',
	},
	auto: true,
})

const defaultTemplate = computed(
	() => settings.data?.default_certificate_template,
)

const columns = computed(() => [
	{ label: __('Name'), key: 'template_name', align: 'left', width: '35%' },
	{ label: __('Type'), key: 'template_type', align: 'left', width: '15%' },
	{ label: __('Page'), key: 'page', align: 'left', width: '25%' },
	{ label: __('Enabled'), key: 'enabled', align: 'center', width: '15%' },
	{ key: 'action', align: 'right' },
])

const getMoreOptions = (row) => [
	{
		label: __('Edit'),
		icon: 'edit',
		onClick: () => openForm(row.name),
	},
	{
		label: __('Set as default'),
		icon: 'check-circle',
		onClick: () => setDefault(row),
	},
	{
		label: __('Delete'),
		icon: 'trash-2',
		onClick: () => deleteTemplate(row),
	},
]

const openForm = (name) => {
	selectedTemplate.value = name
	showForm.value = true
}

const closeForm = () => {
	showForm.value = false
}

const onSaved = () => {
	templates.reload()
	settings.reload()
}

const toggleEnabled = (row, value) => {
	call('frappe.client.set_value', {
		doctype: 'LMS Certificate Template',
		name: row.name,
		fieldname: 'enabled',
		value: value ? 1 : 0,
	})
		.then(() => templates.reload())
		.catch((err) => {
			toast.error(
				cleanError(err.messages?.[0]) || __('Error updating template'),
			)
			templates.reload()
		})
}

const setDefault = (row) => {
	if (!row.enabled) {
		toast.error(__('Enable the template before making it the default'))
		return
	}
	call('frappe.client.set_value', {
		doctype: 'LMS Settings',
		name: 'LMS Settings',
		fieldname: 'default_certificate_template',
		value: row.name,
	})
		.then(() => {
			settings.reload()
			toast.success(__('Default certificate template updated'))
		})
		.catch((err) => {
			toast.error(
				cleanError(err.messages?.[0]) || __('Error updating settings'),
			)
		})
}

const deleteTemplate = (row) => {
	if (!window.confirm(__('Delete the template {0}?').format(row.name))) return
	call('frappe.client.delete', {
		doctype: 'LMS Certificate Template',
		name: row.name,
	})
		.then(() => {
			templates.reload()
			toast.success(__('Certificate template deleted'))
		})
		.catch((err) => {
			toast.error(
				cleanError(err.messages?.[0]) || __('Error deleting template'),
			)
		})
}
</script>
