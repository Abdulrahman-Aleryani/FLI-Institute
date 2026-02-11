<template>
	<div class="flex h-full flex-col">
		<header
			class="sticky top-0 z-10 flex flex-wrap gap-3 items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="breadcrumbs" />
			<div class="flex items-center gap-2 flex-wrap justify-end">
				<Badge
					v-if="sheetDoc"
					:label="sheetDoc.docstatus === 1 ? __('Submitted') : __('Draft')"
					:theme="sheetDoc.docstatus === 1 ? 'green' : 'gray'"
				/>
				<Button variant="outline" @click="reloadSheet" :loading="sheetLoading">
					<template #prefix>
						<RefreshCcw class="h-4 w-4 stroke-1.5" />
					</template>
					{{ __('Reload') }}
				</Button>
				<Button
					v-if="canReopenSheet"
					variant="ghost"
					color="orange"
					:disabled="isReopening"
					:loading="isReopening"
					@click="reopenSheet"
				>
					<template #prefix>
						<Undo2 class="h-4 w-4 stroke-1.5" />
					</template>
					{{ __('Reopen') }}
				</Button>
			</div>
		</header>

		<div class="p-5 pb-10 space-y-6">
			<section v-if="!canAccess" class="max-w-xl mx-auto text-center">
				<EmptyState
					type="Access"
					:title="__('Instructor access required')"
					:message="__('Only assigned instructors or moderators can manage attendance.')"
				/>
			</section>

			<section v-else>
				<div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between mb-6">
					<div>
						<p class="text-sm uppercase tracking-wide text-ink-gray-5">
							{{ __('Attendance for') }}
						</p>
						<h1 class="text-2xl font-semibold text-ink-gray-9">
							{{ batchTitle }}
						</h1>
						<p v-if="sheetDoc" class="text-sm text-ink-gray-5">
							{{ formatRange(sheetDoc.start_date, sheetDoc.end_date) }}
						</p>
						<p v-if="filterSummary" class="text-xs text-ink-gray-4 mt-1">
							{{ filterSummary }}
						</p>
					</div>
					<div class="flex flex-wrap gap-2">
						<Button
							variant="outline"
							:disabled="disableSave"
							:loading="isSaving"
							@click="saveSheet"
						>
							<template #prefix>
								<Save class="h-4 w-4 stroke-1.5" />
							</template>
							{{ __('Save Draft') }}
						</Button>
						<Button
							variant="solid"
							color="green"
							:disabled="disableSubmit"
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

				<div class="grid gap-4 lg:grid-cols-[1.6fr,1fr]">
					<div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 space-y-4">
						<div>
							<p class="text-xs font-semibold text-ink-gray-5 uppercase mb-2">
								{{ __('Week grouping') }}
							</p>
							<div class="flex flex-wrap gap-2">
								<button
									type="button"
									class="rounded-full border px-3 py-1 text-sm transition"
									:class="weekFilter === 'all' ? activeChipClasses : inactiveChipClasses"
									@click="selectWeek('all')"
								>
									{{ __('All weeks') }}
								</button>
								<button
									v-for="week in weeks"
									:key="week.index"
									type="button"
									class="rounded-full border px-3 py-1 text-sm transition"
									:class="weekFilter === week.index ? activeChipClasses : inactiveChipClasses"
									@click="selectWeek(week.index)"
								>
									{{ week.label }}
								</button>
							</div>
						</div>

						<div class="grid gap-4 md:grid-cols-3">
							<div>
								<p class="text-xs font-semibold text-ink-gray-5 uppercase mb-2">
									{{ __('Quick filter') }}
								</p>
								<div class="flex flex-wrap gap-2">
									<button
										v-for="option in quickFilterOptions"
										:key="option.value"
										type="button"
										class="rounded-full border px-3 py-1 text-xs font-medium transition"
										:class="quickFilter === option.value ? activeChipClasses : inactiveChipClasses"
										@click="quickFilter = option.value"
									>
										{{ option.label }}
									</button>
								</div>
							</div>
							<div>
								<p class="text-xs font-semibold text-ink-gray-5 uppercase mb-2">
									{{ __('Status filter') }}
								</p>
								<div class="flex flex-wrap gap-2">
									<button
										v-for="status in statusFilterOptions"
										:key="status.value"
										type="button"
										class="rounded-full border px-3 py-1 text-xs font-medium transition"
										:class="statusFilter === status.value ? activeChipClasses : inactiveChipClasses"
										@click="statusFilter = status.value"
									>
										{{ status.label }}
									</button>
								</div>
							</div>
							<div>
								<p class="text-xs font-semibold text-ink-gray-5 uppercase mb-2">
									{{ __('Search students') }}
								</p>
								<div class="relative">
									<FormControl
										v-model="studentQuery"
										type="text"
										:placeholder="__('Search by name or email')"
									/>
									<Search class="h-4 w-4 text-ink-gray-5 absolute right-3 top-1/2 -translate-y-1/2" />
								</div>
							</div>
						</div>
					</div>

					<div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 space-y-3">
						<div class="flex items-center justify-between">
							<p class="text-sm font-medium text-ink-gray-8">
								{{ __('Sheet notes') }}
							</p>
							<span class="text-xs text-ink-gray-5">{{ __('Optional') }}</span>
						</div>
						<FormControl
							v-model="sheetNotes"
							type="textarea"
							:rows="4"
							:disabled="isReadOnly"
							placeholder="{{ __('Add any instructions or context for this sheet') }}"
						/>
					</div>
				</div>

				<div v-if="batchLoading || sheetLoading" class="space-y-4 mt-6">
					<div class="h-12 rounded-xl border border-outline-gray-2 bg-surface-gray-1 animate-pulse" />
					<div class="h-52 rounded-xl border border-outline-gray-2 bg-surface-gray-1 animate-pulse" />
				</div>

				<template v-else>
					<div
						v-if="!hasSheet"
						class="rounded-xl border border-outline-gray-2 bg-surface-white p-6 text-center text-ink-gray-6 mt-6"
					>
						{{ __('Attendance sheet will appear here once the batch has valid dates and enrollments.') }}
					</div>

					<div
						v-else-if="!hasVisibleDays"
						class="rounded-xl border border-outline-gray-2 bg-surface-white p-6 text-center text-ink-gray-6 mt-6"
					>
						{{ __('No days match the current filters. Adjust the filters to see attendance entries.') }}
					</div>

					<div v-else class="space-y-6 mt-6">
						<section
							v-for="week in visibleWeeks"
							:key="week.index"
							class="rounded-xl border border-outline-gray-2 bg-surface-white"
						>
							<button
								type="button"
								class="flex w-full items-center justify-between px-5 py-4 border-b border-outline-gray-1 text-left"
								@click="toggleWeek(week.index)"
							>
								<div>
									<p class="text-sm font-semibold text-ink-gray-8">
										{{ week.label }}
									</p>
									<p class="text-xs text-ink-gray-5">
										{{ summarizeWeek(week) }}
									</p>
								</div>
								<ChevronDown
									class="h-5 w-5 text-ink-gray-5 transition-transform"
									:class="{ 'rotate-180': !isWeekCollapsed(week.index) }"
								/>
							</button>

							<div v-if="!isWeekCollapsed(week.index)" class="overflow-x-auto">
								<table class="w-full min-w-[900px] text-sm">
									<thead class="bg-surface-gray-1 text-ink-gray-6">
										<tr>
											<th class="sticky left-0 bg-surface-gray-1 px-4 py-3 text-left font-medium w-64">
												{{ __('Student') }}
											</th>
											<th
												v-for="day in week.days"
												:key="day.date"
												class="px-4 py-3 text-left font-medium min-w-[200px]"
											>
												<div class="text-xs uppercase tracking-wide">
													{{ day.weekday }}
												</div>
												<div class="font-semibold text-ink-gray-9">
													{{ formatDayLabel(day.date) }}
												</div>
											</th>
										</tr>
									</thead>
									<tbody>
										<tr
											v-for="row in visibleRows"
											:key="row.enrollment"
											class="border-t border-outline-gray-1"
										>
											<td class="sticky left-0 bg-surface-white px-4 py-3 align-top">
												<div class="font-medium text-ink-gray-8">
													{{ row.student_name || row.student }}
												</div>
												<div class="text-xs text-ink-gray-5">
													{{ row.student }}
												</div>
											</td>
											<td
												v-for="day in week.days"
												:key="`${row.enrollment}-${day.date}`"
												class="px-4 py-3 align-top border-l border-outline-gray-1"
											>
												<div v-if="getEntry(row, day.date)" class="flex flex-col gap-2">
													<div class="grid grid-cols-2 gap-1">
														<button
															v-for="status in attendanceStatuses"
															:key="status.value"
															type="button"
															class="rounded-lg border px-2 py-1 text-xs font-medium transition"
															:class="
																getEntry(row, day.date).status === status.value
																	? 'border-ink-gray-8 bg-surface-green-1 text-ink-gray-9'
																	: 'border-outline-gray-2 text-ink-gray-5'
															"
															:disabled="isReadOnly || isEntrySaving(getEntry(row, day.date))"
															@click="setEntryStatus(row, day, status.value)"
														>
															{{ status.short }}
														</button>
													</div>

													<FormControl
														v-if="getEntry(row, day.date).status === 'Excused'"
														v-model="getEntry(row, day.date).excuse_reason"
														type="textarea"
														:rows="2"
														class="text-xs"
														:disabled="isReadOnly || isEntrySaving(getEntry(row, day.date))"
														placeholder="{{ __('Enter excuse reason') }}"
														@change="() => updateEntryExcuse(getEntry(row, day.date))"
													/>

													<FormControl
														v-model="getEntry(row, day.date).notes"
														type="textarea"
														:rows="2"
														class="text-xs"
														:disabled="isReadOnly || isEntrySaving(getEntry(row, day.date))"
														placeholder="{{ __('Optional notes') }}"
														@change="() => updateEntryNotes(getEntry(row, day.date))"
													/>
												</div>
												<div v-else class="text-xs text-ink-gray-4">
													{{ __('No entry') }}
												</div>
											</td>
										</tr>
										<tr v-if="!visibleRows.length">
											<td
												:colspan="week.days.length + 1"
												class="px-4 py-5 text-center text-ink-gray-4"
											>
												{{ __('No students match the current filters.') }}
											</td>
										</tr>
									</tbody>
								</table>
							</div>
						</section>
					</div>
				</template>
			</section>
		</div>
	</div>
</template>

<script setup>
import { Badge, Breadcrumbs, Button, FormControl, call, toast, usePageMeta } from 'frappe-ui'
import { computed, inject, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, ChevronDown, RefreshCcw, Save, Search, Undo2 } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const user = inject('$user')
const dayjs = inject('$dayjs')
const { brand } = sessionStore()

const batchDoc = ref(null)
const sheetDoc = ref(null)
const sheetName = ref(route.params.sheetName || '')
const batchLoading = ref(false)
const sheetLoading = ref(false)
const isSaving = ref(false)
const isSubmitting = ref(false)
const isReopening = ref(false)
const sheetNotes = ref('')
const weekFilter = ref('all')
const quickFilter = ref('all')
const statusFilter = ref('all')
const studentQuery = ref('')
const collapsedWeeks = reactive({})
const entrySaving = reactive({})

const attendanceStatuses = [
	{ value: 'Present', label: __('Present'), short: __('Present') },
	{ value: 'Absent', label: __('Absent'), short: __('Absent') },
	{ value: 'Late', label: __('Late'), short: __('Late') },
	{ value: 'Excused', label: __('Excused'), short: __('Excused') },
]

const quickFilterOptions = [
	{ value: 'all', label: __('All days') },
	{ value: 'current-week', label: __('Current week') },
	{ value: 'today', label: __('Today') },
	{ value: 'pending', label: __('Only pending') },
]

const statusFilterOptions = [
	{ value: 'all', label: __('All statuses') },
	...attendanceStatuses.map((status) => ({ value: status.value, label: status.label })),
]

const activeChipClasses = 'border-ink-gray-8 bg-surface-gray-1 text-ink-gray-9 shadow-sm'
const inactiveChipClasses = 'border-outline-gray-2 text-ink-gray-5 hover:border-ink-gray-4'

const canAccess = computed(() => {
	const data = user.data
	if (!data) return false
	return (
		data.is_instructor ||
		data.is_moderator ||
		data.roles?.includes('Instructor') ||
		data.roles?.includes('LMS Instructor') ||
		data.roles?.includes('Moderator')
	)
})

const isModeratorOrAdmin = computed(() => {
	const data = user.data
	if (!data) return false
	return (
		data.is_moderator ||
		data.roles?.includes('Moderator') ||
		data.roles?.includes('Administrator') ||
		data.roles?.includes('System Manager')
	)
})

const isReadOnly = computed(() => sheetDoc.value?.docstatus === 1)
const disableSave = computed(() => !sheetDoc.value || isReadOnly.value)
const disableSubmit = computed(
	() => !sheetDoc.value || isReadOnly.value || entrySavingInProgress.value
)
const canReopenSheet = computed(() => isModeratorOrAdmin.value && isReadOnly.value)
const entrySavingInProgress = computed(() =>
	Object.values(entrySaving).some((value) => Boolean(value))
)

const batchTitle = computed(
	() => batchDoc.value?.title || batchDoc.value?.name || route.params.batchName
)

const breadcrumbs = computed(() => [
	{
		label: __('Attendance'),
		route: { name: 'Attendance' },
	},
	{
		label: batchTitle.value,
		route: {
			name: 'BatchAttendance',
			params: {
				batchName: route.params.batchName,
				sheetName: sheetName.value || undefined,
			},
		},
	},
])

const weeks = computed(() => sheetDoc.value?.weeks || [])
const allRows = computed(() => sheetDoc.value?.rows || [])
const today = dayjs().format('YYYY-MM-DD')

const currentWeekIndex = computed(() => {
	for (const week of weeks.value) {
		if (week.days.some((day) => day.date === today)) {
			return week.index
		}
	}
	return null
})

watch(
	() => sheetDoc.value?.notes ?? '',
	(value) => {
		sheetNotes.value = value || ''
	},
	{ immediate: true }
)

watch(
	() => weeks.value,
	(value) => {
		value.forEach((week) => {
			if (collapsedWeeks[week.index] === undefined) {
				collapsedWeeks[week.index] = false
			}
		})
	},
	{ immediate: true }
)

const hasSheet = computed(() => Boolean(sheetDoc.value))

const visibleWeeks = computed(() => {
	const filtered = []
	for (const week of weeks.value) {
		if (weekFilter.value !== 'all' && week.index !== weekFilter.value) continue

		const days = week.days.filter((day) => {
			if (quickFilter.value === 'today') {
				return day.date === today
			}
			if (quickFilter.value === 'current-week') {
				return week.index === currentWeekIndex.value
			}
			if (quickFilter.value === 'pending') {
				return hasPendingOnDay(day.date)
			}
			return true
		})

		if (days.length) {
			filtered.push({ ...week, days })
		}
	}
	return filtered
})

const visibleDates = computed(() => {
	const dates = []
	visibleWeeks.value.forEach((week) => {
		week.days.forEach((day) => dates.push(day.date))
	})
	return dates
})

const visibleRows = computed(() => {
	const query = (studentQuery.value || '').toLowerCase()
	return allRows.value.filter((row) => {
		const matchesQuery =
			!query ||
			row.student?.toLowerCase().includes(query) ||
			row.student_name?.toLowerCase().includes(query)
		if (!matchesQuery) return false

		if (statusFilter.value === 'all') {
			return true
		}

		return visibleDates.value.some(
			(date) => row.entries?.[date]?.status === statusFilter.value
		)
	})
})

const hasVisibleDays = computed(() => visibleDates.value.length > 0)

const filterSummary = computed(() => {
	const parts = []
	if (weekFilter.value !== 'all') {
		const label = weeks.value.find((week) => week.index === weekFilter.value)?.label
		if (label) parts.push(label)
	}
	if (quickFilter.value !== 'all') {
		const label = quickFilterOptions.find((option) => option.value === quickFilter.value)?.label
		if (label) parts.push(label)
	}
	if (statusFilter.value !== 'all') {
		const label = statusFilterOptions.find((option) => option.value === statusFilter.value)?.label
		if (label) parts.push(label)
	}
	return parts.join(' • ')
})

const formatRange = (start, end) => {
	if (!start && !end) return ''
	const formattedStart = start ? dayjs(start).format('MMM DD, YYYY') : __('TBD')
	const formattedEnd = end ? dayjs(end).format('MMM DD, YYYY') : __('TBD')
	return __('{0} – {1}').format(formattedStart, formattedEnd)
}

const formatDayLabel = (date) => dayjs(date).format('MMM DD')

const selectWeek = (weekIndex) => {
	weekFilter.value = weekIndex
}

const toggleWeek = (weekIndex) => {
	collapsedWeeks[weekIndex] = !collapsedWeeks[weekIndex]
}

const isWeekCollapsed = (weekIndex) => collapsedWeeks[weekIndex]

const hasPendingOnDay = (date) => {
	return allRows.value.some((row) => {
		const entry = row.entries?.[date]
		return entry && entry.status !== 'Present'
	})
}

const summarizeWeek = (week) => {
	const totals = {
		Present: 0,
		Absent: 0,
		Late: 0,
		Excused: 0,
	}

	visibleRows.value.forEach((row) => {
		week.days.forEach((day) => {
			const entry = row.entries?.[day.date]
			if (entry) {
				totals[entry.status] += 1
			}
		})
	})

	return __('P:{0} · A:{1} · L:{2} · E:{3}').format(
		totals.Present,
		totals.Absent,
		totals.Late,
		totals.Excused
	)
}

const getEntry = (row, date) => row.entries?.[date]

const isEntrySaving = (entry) => {
	if (!entry?.name) {
		return false
	}
	return Boolean(entrySaving[entry.name])
}

const requestExcuseReason = async (entry) => {
	if (typeof window === 'undefined') return ''
	const message =
		entry.excuse_reason && entry.excuse_reason.trim().length
			? __('Update excuse reason')
			: __('Provide an excuse reason')
	const value = window.prompt(message, entry.excuse_reason || '')
	return (value || '').trim()
}

const setEntryStatus = async (row, day, status) => {
	const entry = getEntry(row, day.date)
	if (!entry || isReadOnly.value || entry.status === status) return

	const previous = { status: entry.status, excuse_reason: entry.excuse_reason }
	entry.status = status
	if (status !== 'Excused') {
		entry.excuse_reason = ''
	} else if (!entry.excuse_reason || !entry.excuse_reason.trim()) {
		const reason = await requestExcuseReason(entry)
		if (!reason) {
			entry.status = previous.status
			entry.excuse_reason = previous.excuse_reason
			toast.error(__('Excuse reason is required for excused absences.'))
			return
		}
		entry.excuse_reason = reason
	}

	try {
		await persistEntry(entry, {
			status: entry.status,
			excuse_reason: entry.excuse_reason,
			notes: entry.notes,
		})
	} catch (error) {
		entry.status = previous.status
		entry.excuse_reason = previous.excuse_reason
		toast.error(error?.message || __('Failed to update attendance'))
	}
}

const updateEntryExcuse = async (entry) => {
	if (!entry || isReadOnly.value) return
	try {
		await persistEntry(entry, {
			status: entry.status,
			excuse_reason: entry.excuse_reason,
			notes: entry.notes,
		})
	} catch (error) {
		toast.error(error?.message || __('Failed to save excuse reason'))
	}
}

const updateEntryNotes = async (entry) => {
	if (!entry || isReadOnly.value) return
	try {
		await persistEntry(entry, {
			status: entry.status,
			excuse_reason: entry.excuse_reason,
			notes: entry.notes,
		})
	} catch (error) {
		toast.error(error?.message || __('Failed to save notes'))
	}
}

const persistEntry = async (entry, payload) => {
	if (!entry?.name) return
	entrySaving[entry.name] = true
	try {
		await call('lms.lms.api.attendance.update_attendance_entry', {
			entry_name: entry.name,
			status: payload.status,
			excuse_reason: payload.excuse_reason,
			notes: payload.notes,
		})
	} finally {
		entrySaving[entry.name] = false
	}
}

const fetchBatch = async () => {
	if (!route.params.batchName) return
	batchLoading.value = true
	try {
		const doc = await call('lms.lms.api.attendance.get_batch_summary', {
			batch: route.params.batchName,
		})
		batchDoc.value = doc
	} catch (error) {
		console.error(error)
		toast.error(error?.message || __('Failed to load batch information.'))
	} finally {
		batchLoading.value = false
	}
}

const setSheetDoc = (doc) => {
	if (!doc) {
		sheetDoc.value = null
		return
	}
	sheetDoc.value = doc
	if (doc.name) {
		sheetName.value = doc.name
		router.replace({
			name: 'BatchAttendance',
			params: {
				batchName: route.params.batchName,
				sheetName: doc.name,
			},
		})
	}
}

const loadSheet = async () => {
	if (!route.params.batchName) return
	sheetLoading.value = true
	try {
		const sheet = await call('lms.lms.api.attendance.get_or_create_sheet', {
			batch: route.params.batchName,
		})
		setSheetDoc(sheet)
	} catch (error) {
		console.error(error)
		toast.error(error?.message || __('Failed to load attendance sheet.'))
	} finally {
		sheetLoading.value = false
	}
}

const reloadSheet = async () => {
	await loadSheet()
}

const saveSheet = async () => {
	if (!sheetDoc.value || isReadOnly.value) return
	isSaving.value = true
	try {
		await call('lms.lms.api.attendance.save_sheet', {
			name: sheetDoc.value.name,
			notes: sheetNotes.value,
		})
		toast.success(__('Sheet saved as draft'))
	} catch (error) {
		console.error(error)
		toast.error(error?.message || __('Failed to save sheet'))
	} finally {
		isSaving.value = false
	}
}

const submitSheet = async () => {
	if (!sheetDoc.value || isReadOnly.value) return
	isSubmitting.value = true
	try {
		const submitted = await call('lms.lms.api.attendance.submit_sheet', {
			name: sheetDoc.value.name,
		})
		setSheetDoc(submitted)
		toast.success(__('Attendance submitted'))
	} catch (error) {
		console.error(error)
		toast.error(error?.message || __('Failed to submit sheet'))
	} finally {
		isSubmitting.value = false
	}
}

const reopenSheet = async () => {
	if (!sheetDoc.value) return
	isReopening.value = true
	try {
		const reopened = await call('lms.lms.api.attendance.reopen_sheet', {
			name: sheetDoc.value.name,
		})
		setSheetDoc(reopened)
		toast.success(__('Attendance sheet reopened'))
	} catch (error) {
		console.error(error)
		toast.error(error?.message || __('Failed to reopen sheet'))
	} finally {
		isReopening.value = false
	}
}

const initialize = async () => {
	await fetchBatch()
	await loadSheet()
}

onMounted(() => {
	if (canAccess.value) {
		initialize()
	}
})

usePageMeta(() => ({
	title: __('Attendance'),
	icon: brand.favicon,
}))
</script>
