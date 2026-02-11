<template>
	<div class="flex h-full flex-col">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="breadcrumbs" />
			<div class="flex items-center gap-2">
				<Badge
					v-if="gradeSheet"
					:label="gradeSheet.docstatus === 1 ? __('Submitted') : __('Draft')"
					:theme="gradeSheet.docstatus === 1 ? 'green' : 'gray'"
				/>
				<Button @click="reloadSheet" :loading="sheetResource.loading">
					<template #prefix>
						<RefreshCcw class="h-4 w-4 stroke-1.5" />
					</template>
					{{ __('Reload') }}
				</Button>
			</div>
		</header>

		<div class="p-5 pb-10 space-y-6">
			<section v-if="sheetResource.loading" class="space-y-4">
				<div
					v-for="i in 4"
					:key="i"
					class="h-16 rounded-xl border border-outline-gray-2 bg-surface-gray-1 animate-pulse"
				/>
			</section>

			<section v-else-if="!gradeSheet">
				<EmptyState
					type="Document"
					:title="__('No grade sheet found')"
					:message="__('We could not load the grade sheet for this batch. Please try again.')"
				/>
			</section>

			<section v-else class="space-y-5">
				<div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
					<div>
						<h1 class="text-2xl font-semibold text-ink-gray-9">
							{{ sheetTitle }}
						</h1>
						<p class="text-sm text-ink-gray-5">
							{{ __('Instructor: {0}').format(instructorDisplayName) }}
						</p>
					</div>
					<div class="flex flex-wrap gap-2">
						<Button variant="outline" :disabled="isReadOnly || isSaving" :loading="isSaving" @click="saveSheet">
							<template #prefix>
								<Save class="h-4 w-4 stroke-1.5" />
							</template>
							{{ __('Save Draft') }}
						</Button>
						<Button
							variant="solid"
							color="green"
							:disabled="isReadOnly || isSubmitting"
							:loading="isSubmitting"
							@click="submitSheet"
						>
							<template #prefix>
								<Check class="h-4 w-4 stroke-1.5" />
							</template>
							{{ __('Submit') }}
						</Button>
					</div>
				</div>

				<div
					v-if="gradeSheet.docstatus === 1"
					class="rounded-lg border border-outline-gray-2 bg-surface-green-1 px-4 py-3 text-sm text-ink-green-8"
				>
					{{ __('This grade sheet has been submitted and is read-only.') }}
				</div>

				<div
					v-if="totalsWarning"
					class="rounded-lg border border-outline-red-2 bg-surface-red-1 px-4 py-3 text-sm text-ink-red-7"
				>
					{{ __('One or more students exceed the maximum total of 100. Please adjust before submitting.') }}
				</div>

				<div
					v-if="validationErrors.length"
					class="space-y-2 rounded-lg border border-outline-red-2 bg-surface-red-1 px-4 py-3 text-sm text-ink-red-8"
				>
					<div class="font-medium">{{ __('Submission blocked') }}</div>
					<ul class="list-disc space-y-1 pl-5">
						<li v-for="(err, idx) in validationErrors" :key="`${err}-${idx}`">
							{{ err }}
						</li>
					</ul>
				</div>

				<div class="overflow-x-auto rounded-xl border border-outline-gray-2 bg-surface-white">
					<table class="w-full min-w-[900px] text-sm">
						<thead class="bg-surface-gray-1 text-ink-gray-6">
							<tr>
								<th class="px-4 py-3 text-left font-medium">{{ __('Student') }}</th>
								<th
									v-for="field in gradeFields"
									:key="field"
									class="px-2 py-3 text-center font-medium"
								>
									{{ gradeLabels[field] }}<br />
									<span class="text-xs text-ink-gray-4">/ {{ gradeMax[field] }}</span>
								</th>
								<th class="px-4 py-3 text-center font-medium">{{ __('Total') }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in tableRows" :key="row.name || row.student" class="border-t border-outline-gray-1">
								<td class="px-4 py-3">
									<div class="font-medium text-ink-gray-8">
										{{ row.student_name || row.student }}
									</div>
									<div class="text-xs text-ink-gray-5">{{ row.student }}</div>
								</td>
								<td
									v-for="field in gradeFields"
									:key="`${row.student}-${field}`"
									class="px-2 py-3 text-center"
								>
									<FormControl
										v-model="row[field]"
										type="number"
										:min="0"
										:max="gradeMax[field]"
										:step="0.5"
										:disabled="isReadOnly"
										@input="onFieldChange(row, field)"
									/>
								</td>
								<td class="px-4 py-3 text-center">
									<span
										class="font-semibold"
										:class="(row.total || 0) > MAX_TOTAL ? 'text-ink-red-6' : 'text-ink-gray-8'"
									>
										{{ formatNumber(row.total) }}
									</span>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</section>
		</div>
	</div>
</template>

<script setup>
import { Badge, Breadcrumbs, Button, FormControl, call, createResource, toast } from 'frappe-ui'
import { computed, inject, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, RefreshCcw, Save } from 'lucide-vue-next'
import EmptyState from '@/components/EmptyState.vue'

const MAX_TOTAL = 100
const gradeFields = [
	'attendance',
	'participation',
	'assignments',
	'speaking',
	'writing',
	'communicative_competence',
	'final_oral',
	'exam',
]

const gradeLabels = {
	attendance: __('Attendance'),
	participation: __('Participation'),
	assignments: __('Assignments'),
	speaking: __('Speaking'),
	writing: __('Writing'),
	communicative_competence: __('Comm. Competence'),
	final_oral: __('Final Oral'),
	exam: __('Exam'),
}

const gradeMax = {
	attendance: 10,
	participation: 10,
	assignments: 10,
	speaking: 10,
	writing: 15,
	communicative_competence: 10,
	final_oral: 10,
	exam: 25,
}

const route = useRoute()
const router = useRouter()
const user = inject('$user')

const gradeSheet = ref(null)
const sheetName = ref(route.params.sheetName || '')
const instructorName = ref('')
const totalsWarning = ref(false)
const validationErrors = ref([])
const isSaving = ref(false)
const isSubmitting = ref(false)

const sheetResource = createResource({
	url: 'frappe.client.get',
	makeParams(values) {
		return {
			doctype: 'Batch Grade Sheet',
			name: values.name,
		}
	},
	auto: false,
	onSuccess(data) {
		gradeSheet.value = {
			...data,
			grade_records: (data.grade_records || []).map((row) => ({ ...row })),
		}
		instructorName.value = data.instructor_name || data.instructor
		if (!gradeSheet.value.grade_records.length) {
			populateStudents()
		} else {
			recalculateAllTotals()
		}
	},
})

const tableRows = computed(() => gradeSheet.value?.grade_records || [])
const isReadOnly = computed(() => gradeSheet.value?.docstatus === 1)
const sheetTitle = computed(() => gradeSheet.value?.batch_title || route.params.batchName)
const instructorDisplayName = computed(
	() => instructorName.value || user.data?.full_name || user.data?.name || __('Unknown Instructor')
)

const breadcrumbs = computed(() => [
	{ label: __('Grading'), route: { name: 'Grading' } },
	{
		label: sheetTitle.value,
		route: {
			name: 'BatchGrading',
			params: { batchName: route.params.batchName, sheetName: sheetName.value },
		},
	},
])

onMounted(async () => {
	await ensureSheetName()
	reloadSheet()
})

const ensureSheetName = async () => {
	if (sheetName.value) return sheetName.value
	const sheet = await callWithError('lms.lms.api.get_or_create_grade_sheet', {
		batch_name: route.params.batchName,
	})
	if (sheet?.name) {
		sheetName.value = sheet.name
		router.replace({
			name: 'BatchGrading',
			params: { batchName: route.params.batchName, sheetName: sheetName.value },
		})
	}
	return sheetName.value
}

const reloadSheet = () => {
	if (!sheetName.value) return
	sheetResource.reload({ name: sheetName.value })
}

const populateStudents = async () => {
	const students = await callWithError('lms.lms.api.get_enrolled_students', {
		batch_name: route.params.batchName,
	})
	if (!Array.isArray(students)) return
	gradeSheet.value.grade_records = students.map((student, idx) => {
		const record = {
			idx: idx + 1,
			student: student.student,
			student_name: student.student_name,
			doctype: 'Batch Grade Record',
			parenttype: 'Batch Grade Sheet',
			parentfield: 'grade_records',
			total: 0,
		}
		gradeFields.forEach((field) => {
			record[field] = null
		})
		return record
	})
	recalculateAllTotals()
}

const onFieldChange = (row, field) => {
	const raw = row[field]
	if (raw === '' || raw === null || raw === undefined) {
		row[field] = null
	} else {
		const numeric = Number(raw)
		row[field] = Number.isFinite(numeric) ? numeric : null
	}
	recalculateRowTotal(row)
}

const recalculateRowTotal = (row) => {
	let total = 0
	gradeFields.forEach((field) => {
		const value = Number(row[field]) || 0
		total += value
	})
	row.total = Number(total.toFixed(2))
	updateTotalsWarning()
}

const recalculateAllTotals = () => {
	tableRows.value.forEach((row) => recalculateRowTotal(row))
	updateTotalsWarning()
}

const updateTotalsWarning = () => {
	totalsWarning.value = tableRows.value.some((row) => (row.total || 0) > MAX_TOTAL)
}

const formatNumber = (value) => {
	if (value === null || value === undefined) return '--'
	return Number(value).toFixed(2)
}

const serializeDoc = () => {
	if (!gradeSheet.value) return {}
	return {
		...gradeSheet.value,
		grade_records: tableRows.value.map((row) => ({
			...row,
			doctype: 'Batch Grade Record',
			parent: gradeSheet.value.name,
			parentfield: 'grade_records',
			parenttype: 'Batch Grade Sheet',
		})),
	}
}

const saveSheet = async () => {
	if (!gradeSheet.value) return
	isSaving.value = true
	validationErrors.value = []
	try {
		const saved = await callWithError('frappe.client.save', { doc: serializeDoc() })
		if (saved) {
			gradeSheet.value = normalizeDoc(saved)
			recalculateAllTotals()
			toast.success(__('Grade sheet saved'))
		}
	} finally {
		isSaving.value = false
	}
}

const submitSheet = async () => {
	if (!gradeSheet.value) return
	isSubmitting.value = true
	validationErrors.value = []
	try {
		const submitted = await callWithError('frappe.client.submit', { doc: serializeDoc() })
		if (submitted) {
			gradeSheet.value = normalizeDoc(submitted)
			recalculateAllTotals()
			toast.success(__('Grade sheet submitted'))
		}
	} catch (error) {
		captureValidationErrors(error)
		throw error
	} finally {
		isSubmitting.value = false
	}
}

const normalizeDoc = (doc) => ({
	...doc,
	grade_records: (doc.grade_records || []).map((row) => ({ ...row })),
})

const captureValidationErrors = (error) => {
	const messages = error?.messages || []
	if (!messages.length && error?.exc_type) {
		validationErrors.value = [error.exception || __('Submission failed')]
		return
	}
	validationErrors.value = messages
}

const callWithError = async (method, params = {}, { silent = false } = {}) => {
	try {
		return await call(method, params)
	} catch (error) {
		if (!silent) {
			toast.error(error.messages?.[0] || error.message || __('Something went wrong'))
		}
		throw error
	}
}
</script>
