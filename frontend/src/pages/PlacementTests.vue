<template>
	<div class="">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs
				class="h-7"
				:items="[{ label: __('Placement Tests'), route: { name: 'PlacementTests' } }]"
			/>
			<div class="flex items-center gap-2">
				<Button variant="solid" @click="openCreateInDesk()">
					{{ __('Create') }}
				</Button>
				<Button @click="reload()">
					{{ __('Refresh') }}
				</Button>
			</div>
		</header>

		<div class="p-5">
			<div class="max-w-4xl mx-auto">
				<div class="flex items-center justify-between mb-4">
					<div class="text-xl font-semibold text-ink-gray-7">
						{{ __('Placement Tests') }}
					</div>
					<div class="text-sm text-ink-gray-5">
						{{ __('{0} records').format(tests.data?.length || 0) }}
					</div>
				</div>

				<div v-if="tests.loading" class="text-ink-gray-5">
					{{ __('Loading...') }}
				</div>

				<div v-else-if="!tests.data?.length" class="text-ink-gray-5">
					{{ __('No placement tests found.') }}
				</div>

				<div v-else class="overflow-x-auto">
					<table class="w-full border rounded-md">
						<thead class="bg-surface-gray-2 text-ink-gray-7 text-sm">
							<tr>
								<th class="text-left p-2">{{ __('Title') }}</th>
								<th class="text-left p-2">{{ __('Active') }}</th>
								<th class="text-left p-2">{{ __('Last Modified') }}</th>
								<th class="text-right p-2">{{ __('Actions') }}</th>
							</tr>
						</thead>
						<tbody>
							<tr
								v-for="test in tests.data"
								:key="test.name"
								class="border-t"
							>
								<td class="p-2">
									<div class="font-medium text-ink-gray-9">
										{{ test.test_title || test.name }}
									</div>
									<div class="text-xs text-ink-gray-5">{{ test.name }}</div>
								</td>
								<td class="p-2 text-ink-gray-7">
									{{ test.is_active ? __('Yes') : __('No') }}
								</td>
								<td class="p-2 text-ink-gray-7">
									{{ test.modified || '' }}
								</td>
								<td class="p-2 text-right">
									<Button size="sm" @click="openInDesk(test.name)">
										{{ __('Open in Desk') }}
									</Button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { Breadcrumbs, Button, createResource, usePageMeta } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const { brand } = sessionStore()

const tests = createResource({
	url: 'frappe.client.get_list',
	cache: ['placement-tests'],
	makeParams() {
		return {
			doctype: 'Placement Test',
			fields: ['name', 'test_title', 'is_active', 'modified'],
			order_by: 'modified desc',
			limit_page_length: 50,
		}
	},
	auto: true,
})

function reload() {
	tests.reload()
}

function openCreateInDesk() {
	window.location.href = '/app/placement-test/new'
}

function openInDesk(name) {
	window.location.href = `/app/placement-test/${name}`
}

usePageMeta(() => {
	return {
		title: __('Placement Tests'),
		icon: brand.favicon,
	}
})
</script>
